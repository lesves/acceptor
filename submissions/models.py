from django.db import models
from django.db.models import Max
from django.db.models.expressions import F

from django.contrib.auth.models import User

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.urls import reverse

from pathlib import Path
import uuid

import bleach


ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS + ["p", "u", "br"]


def current_year():
	"""Helper function for a default year"""
	return timezone.now().year


def upload_path(instance, filename):
	"""Helper function. Return the upload path for a file submission."""
	return Path(str(instance.thesis.pk)) / filename


class RootSubjectManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().filter(parent=None)


class Subject(models.Model):
	title = models.CharField(max_length=64, verbose_name="Název")
	parent = models.ForeignKey(
		"Subject", 
		related_name="children", 
		on_delete=models.SET_NULL,
		null=True, blank=True,
		verbose_name="Rodičovský předmět"
	)

	# Managers
	objects = models.Manager()
	roots = RootSubjectManager()

	def __str__(self):
		if self.parent:
			return f"{self.parent}, {self.title}"
		return self.title

	@property
	def root(self):
		node = self
		while node.parent:
			node = node.parent
		return node

	def flattree(self):
		"""Return a flattened tree with starting with this subject node"""
		stack = [self]
		while stack:
			subj = stack.pop()
			yield subj
			stack.extend(subj.children.all())

	def inherited_periods(self):
		node = self
		periods = node.periods.all()
		while node.parent:
			node = node.parent
			periods = periods.union(node.periods.all())
		return periods

	class Meta:
		verbose_name = "Předmět"
		verbose_name_plural = "Předměty"


class Keyword(models.Model):
	title = models.CharField(max_length=255, verbose_name="Název")

	def __str__(self):
		return self.title

	class Meta:
		verbose_name = "Klíčové slovo"
		verbose_name_plural = "Klíčová slova"


class StateFilterManager(models.Manager):
	def __init__(self, **kwargs):
		self.kwargs = kwargs
		super().__init__()

	def get_queryset(self):
		return (super()
			.get_queryset()
			.alias(
				latest_logentry_date=Max("log_entries__timestamp")
			).filter(
				log_entries__timestamp=F("latest_logentry_date"),
				**self.kwargs,
			))


class Thesis(models.Model):
	MARK_CHOICES = [
		(1, "výborně"),
		(2, "chvalitebně"),
		(3, "dobře"),
		(4, "dostatečně"),
		(5, "nedostatečně"),
	]

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	# Author fields
	author = models.ForeignKey(
		User, 
		related_name="authored", 
		on_delete=models.PROTECT, 
		null=True, blank=True, 
		verbose_name="Autor"
	)
	supervisor = models.ForeignKey(
		User, 
		related_name="supervised", 
		on_delete=models.PROTECT, 
		null=True, blank=True, 
		verbose_name="Vedoucí"
	)
	opponent = models.ForeignKey(User, 
		related_name="opposed", 
		on_delete=models.PROTECT, 
		null=True, blank=True, 
		verbose_name="Oponent"
	)

	# Informative fields
	title = models.CharField(max_length=255, verbose_name="Název")
	abstract = models.TextField(
		null=True, blank=True, 
		verbose_name="Abstrakt"
	)
	keywords = models.ManyToManyField(
		Keyword, 
		blank=True, 
		verbose_name="Klíčová slova"
	)

	year = models.IntegerField(default=current_year, verbose_name="Ročník")

	# Assignment related fields
	assignment = models.TextField(
		null=True, blank=True, 
		verbose_name="Zadání"
	)

	# Defense related fields
	supervisor_opinion = models.TextField(
		null=True, blank=True, 
		verbose_name="Posudek vedoucího"
	)
	opponent_opinion = models.TextField(
		null=True, blank=True, 
		verbose_name="Posudek oponenta"
	)

	mark = models.PositiveSmallIntegerField(
		null=True, blank=True, 
		choices=MARK_CHOICES, 
		verbose_name="Známka"
	)

	subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="theses", verbose_name="Předmět")

	# Managers
	objects = models.Manager()
	not_closed = StateFilterManager(log_entries__state__is_closed=False)
	closed = StateFilterManager(log_entries__state__is_closed=True)
	public = StateFilterManager(log_entries__state__is_public=True)

	def save(self, **kwargs):
		if self.abstract:
			self.abstract = bleach.clean(self.abstract, tags=ALLOWED_TAGS)
		if self.assignment:
			self.assignment = bleach.clean(self.assignment, tags=ALLOWED_TAGS)
		if self.supervisor_opinion:
			self.supervisor_opinion = bleach.clean(self.supervisor_opinion, tags=ALLOWED_TAGS)
		if self.opponent_opinion:
			self.opponent_opinion = bleach.clean(self.opponent_opinion, tags=ALLOWED_TAGS)

		super().save(**kwargs)

	def get_absolute_url(self):
		return reverse("thesis-detail", kwargs={"pk": self.pk})

	def __str__(self):
		if not self.author:
			return f"nepřiřazen: {self.title}"
		return f"{self.author.get_full_name()}: {self.title}"

	# Utility methods

	def set_state(self, state, user):
		"""Add a new log entry for setting the state"""
		return LogEntry(thesis=self, state=state, user=user).save()

	def set_state_code(self, state_code, user):
		"""Add a new log entry for setting the state with the given code"""
		return self.set_state(State.objects.get(code=state_code), user)

	# Computed properties and methods

	@property
	def last_log_entry(self):
		try:
			return self.log_entries.latest("timestamp")
		except LogEntry.DoesNotExist:
			return None

	@property
	def state(self):
		"""Return the current state of the thesis or None"""
		entry = self.last_log_entry
		if entry is None:
			return None
		return entry.state

	@property
	def mark_verbose(self):
		for m, name in self.MARK_CHOICES:
			if self.mark == m:
				return name
		return "-"

	state.fget.short_description = "Aktuální stav"

	def firstpdf(self):
		"""Return the first pdf in the submission. Used for preview."""
		return self.attachments.filter(file__upload__endswith=".pdf").first()

	def periods(self):
		"""Get the consultation periods and corresponding consultations as a dictionary"""
		dct = {}
		for period in self.subject.inherited_periods():
			dct[period] = self.consultations.filter(thesis=self, period=period)
		return dct

	@classmethod
	def current_of(cls, user):
		"""Return a set of current theses of the given user"""
		y = current_year()

		return (user.authored.filter(year=y)
			.union(user.supervised.filter(year=y))
			.union(user.opposed.filter(year=y)))

	@classmethod
	def public_years(cls):
		"""Return the years in which there are some public theses."""
		return cls.public.order_by("-year").values_list("year", flat=True).distinct()

	# State transitions

	def assignment_update(self, user):
		if self.state.is_approved:
			return False
		if user == self.author:
			if self.state.code == "supervisor_approved":
				self.set_state_code("author_approved", user)
			return True
		elif user == self.supervisor:
			if self.state.code == "author_approved":
				self.set_state_code("supervisor_approved", user)
			return True

		return False

	def approve(self, user):
		if self.state.is_approved:
			return False

		if user == self.author and user == self.supervisor:
			self.set_state_code("approved", user)
			return True
		elif user == self.author:
			if self.state.code == "supervisor_approved":
				self.set_state_code("approved", user)
				return True
		elif user == self.supervisor:
			if self.state.code == "author_approved":
				self.set_state_code("approved", user)
				return True
		return False

	def submit(self, user):
		if not self.state.submittable or user != self.author:
			return False
		self.set_state_code("submitted", self.author)
		return True

	def cancel_submit(self, user):
		if (not self.state.is_submitted or 
				self.state.is_closed or 
				user != self.author):
			return False
		self.set_state_code("approved", self.author)
		return True

	def opinion_added(self, user):
		if self.state.is_closed:
			return False

		if self.supervisor_opinion and self.opponent_opinion:
			self.set_state_code("defense_ready", user)

		return True

	class Meta:
		verbose_name = "Práce"
		verbose_name_plural = "Práce"

		permissions = [
			("author", "Může být autor"),
			("supervisor", "Může být vedoucí"),
			("opponent", "Může být oponent"),
		]


class State(models.Model):
	code = models.CharField(
		primary_key=True, 
		max_length=32, 
		verbose_name="Interní kód")

	name = models.CharField(max_length=32, verbose_name="Název")
	description = models.TextField()

	is_approved = models.BooleanField(default=True, verbose_name="Zadání schváleno?")
	is_submitted = models.BooleanField(default=True, verbose_name="Práce odevzdána?")
	is_closed = models.BooleanField(default=False, verbose_name="Práce uzavřena?")
	is_public = models.BooleanField(default=False, verbose_name="Práce zveřejněná?")

	@property
	def submittable(self):
		return self.is_approved and not self.is_submitted

	def __str__(self):
		return self.name

	class Meta:
		verbose_name = "Stav"
		verbose_name_plural = "Stavy"


class LogEntry(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	state = models.ForeignKey(
		State, 
		related_name="log_entries", 
		on_delete=models.PROTECT,
		verbose_name="Stav")
	thesis = models.ForeignKey(
		Thesis, 
		related_name="log_entries", 
		on_delete=models.CASCADE,
		verbose_name="Práce")

	user = models.ForeignKey(
		User, 
		related_name="log_entries", 
		on_delete=models.SET_NULL, 
		verbose_name="Měnil",
		null=True)
	timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Čas")

	def __str__(self):
		return f"Uživatel {self.user} změnil stav práce {self.thesis} na {self.state}"

	class Meta:
		verbose_name = "Záznam"
		verbose_name_plural = "Záznamy"


class ConsultationPeriod(models.Model):
	"""A period in which `count` consultations must take place."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	subject = models.ForeignKey(
		Subject, 
		related_name="periods", 
		on_delete=models.CASCADE, 
		verbose_name="Předmět")
	count = models.PositiveSmallIntegerField(
		default=1, 
		verbose_name="Počet potřebných konzultací")
	start = models.DateField(verbose_name="Začátek")
	end = models.DateField(verbose_name="Konec")

	def __str__(self):
		return f"{self.subject}: {self.start} - {self.end}"

	class Meta:
		verbose_name = "Období povinných konzultací"
		verbose_name_plural = "Období povinných konzultací"


class Consultation(models.Model):
	"""A thesis consultation"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	thesis = models.ForeignKey(
		Thesis, 
		related_name="consultations", 
		on_delete=models.CASCADE, 
		verbose_name="Práce")
	period = models.ForeignKey(
		ConsultationPeriod, 
		related_name="consultations", 
		on_delete=models.SET_NULL, 
		null=True, 
		verbose_name="Období")
	date = models.DateField(verbose_name="Datum")
	note = models.TextField(blank=True, verbose_name="Poznámky")

	def __str__(self):
		return f"Konzultace {self.date}"

	def save(self, **kwargs):
		self.note = bleach.clean(self.note, tags=ALLOWED_TAGS)

		super().save(**kwargs)

	class Meta:
		verbose_name = "Konzultace"
		verbose_name_plural = "Konzultace"


class SubmissionAttachment(models.Model):
	"""
		A submission attachment, uses multi-table inheritance
		to distinguish between different types of attachments.
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	thesis = models.ForeignKey(Thesis, related_name="attachments", on_delete=models.CASCADE)


class File(SubmissionAttachment):
	"""A file attachment"""
	upload = models.FileField(upload_to=upload_path)

	def __str__(self):
		return Path(self.upload.name).name

	# Imports only used here
	from django.db.models.signals import pre_delete
	from django.dispatch import receiver
	@staticmethod
	@receiver(pre_delete, sender=SubmissionAttachment)
	def delete_handler(sender, **kwargs):
		if File.objects.filter(submissionattachment_ptr=kwargs["instance"]).exists() and kwargs["instance"].file.upload.name:
			try:
				parent = Path(kwargs["instance"].file.upload.path).parent
				kwargs["instance"].file.upload.delete()
				try:
					next(parent.iterdir())
				except StopIteration:
					parent.rmdir()
			except ValueError:
				pass


class Link(SubmissionAttachment):
	"""A link attachment"""
	url = models.URLField()

	def __str__(self):
		return self.url

from django.db import models
from django.contrib.auth.models import User
import uuid

import bleach


def current_year():
	"""Helper function for a default year"""
	return timezone.now().year

def upload_path(instance, filename):
	"""Helper function. Return the upload path for a file submission."""
	return Path(str(instance.thesis.pk)) / filename


class Subject(models.Model):
	title = models.CharField(max_length=64, verbose_name="Název")

	def __str__(self):
		return self.title

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
		verbose_name="Autor")
	supervisor = models.ForeignKey(
		User, 
		related_name="supervised", 
		on_delete=models.PROTECT, 
		null=True, blank=True, 
		verbose_name="Vedoucí")
	opponent = models.ForeignKey(User, 
		related_name="opposed", 
		on_delete=models.PROTECT, 
		null=True, blank=True, 
		verbose_name="Oponent")

	# Informative fields
	title = models.CharField(max_length=255, verbose_name="Název")
	abstract = models.TextField(
		null=True, blank=True, 
		verbose_name="Abstrakt")
	keywords = models.ManyToManyField(
		Keyword, 
		blank=True, 
		verbose_name="Klíčová slova")

	year = models.IntegerField(default=current_year, verbose_name="Ročník")

	# Assignment related fields
	assignment = models.TextField(
		null=True, blank=True, 
		verbose_name="Zadání")

	# Submission related fields
	submission_date = models.DateTimeField(
		null=True, blank=True, 
		verbose_name="Datum a čas odevzdání")

	# Defense related fields
	supervisor_opinion = models.TextField(
		null=True, blank=True, 
		verbose_name="Posudek vedoucího")
	opponent_opinion = models.TextField(
		null=True, blank=True, 
		verbose_name="Posudek oponenta")

	#is_postponed = models.BooleanField(default=False, verbose_name="Odložena?")
	mark = models.PositiveSmallIntegerField(
		null=True, blank=True, 
		choices=MARK_CHOICES, 
		verbose_name="Známka")

	subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="theses", verbose_name="Předmět")

	ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS + ["p", "u"]

	def save(self, **kwargs):
		if self.abstract:
			self.abstract = bleach.clean(self.abstract, self.ALLOWED_TAGS)
		if self.assignment:
			self.assignment = bleach.clean(self.assignment, tags=self.ALLOWED_TAGS)
		if self.supervisor_opinion:
			self.supervisor_opinion = bleach.clean(self.supervisor_opinion, tags=self.ALLOWED_TAGS)
		if self.opponent_opinion:
			self.opponent_opinion = bleach.clean(self.opponent_opinion, tags=self.ALLOWED_TAGS)
		super().save(**kwargs)

	def get_absolute_url(self):
		return reverse("thesis-detail", kwargs={"pk": self.pk})

	def __str__(self):
		return f"{self.author}: {self.title}"

	class Meta:
		verbose_name = "Práce"
		verbose_name_plural = "Práce"


class State(models.Model):
	code = models.CharField(
		primary_key=True, 
		max_length=32, 
		verbose_name="Interní kód")

	name = models.CharField(max_length=32, verbose_name="Název")
	description = models.TextField()

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
	timestamp = models.DateTimeField(auto_created=True, verbose_name="Čas")

	def __str__(self):
		return f"Uživatel {self.user} změnil stav práce {self.thesis} na {self.state}"

	class Meta:
		verbose_name = "Záznam"
		verbose_name_plural = "Záznamy"


class ConsultationPeriod(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	"""A period in which `count` consultations must take place."""
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
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	"""A thesis consultation"""
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

	def __str__(self):
		return f"Konzultace {self.date}"

	class Meta:
		verbose_name = "Konzultace"
		verbose_name_plural = "Konzultace"


class SubmissionAttachment(models.Model):
	"""
		A submission attachment, uses multi-table inheritance
		to distinguish between different types of attachments.
	"""
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
		if File.objects.filter(submission_ptr=kwargs["instance"]).exists() and kwargs["instance"].file.upload.name:
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

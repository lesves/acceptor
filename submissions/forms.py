from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q

from . import models
from .models import Thesis, Keyword
from .utils import split_person_name

from datetime import date


class ConsultationForm(forms.ModelForm):
	date = forms.DateField(
		initial=date.today, 
		widget=forms.SelectDateWidget(years=range(date.today().year-10, date.today().year+10))
	)

	def __init__(self, *args, **kwargs):
		self.thesis = kwargs.pop("thesis")

		super().__init__(*args, **kwargs)

		self.fields["period"].queryset = models.ConsultationPeriod.objects.filter(
			pk__in=(x.pk for x in self.thesis.subject.inherited_periods())
		)

	class Meta:
		model = models.Consultation
		fields = ["period", "date", "note"]


class KeywordWidget(forms.TextInput):
	"""A widget for KeywordUpdateField and KeywordField"""
	def format_value(self, value):
		if value is None:
			return ""
		return ", ".join(map(str, value))

	def value_from_datadict(self, data, files, name):
		if data.get(name):
			return [x.strip() for x in data.get(name).split(",")]


class KeywordUpdateField(forms.Field):
	"""A form field used for updating the keywords of a thesis"""
	widget = KeywordWidget

	def to_python(self, value):
		if not value:
			return []

		res = []
		for title in value:
			k = Keyword.objects.get_or_create(title=title)[0]
			res.append(k)
		return res


class KeywordField(forms.Field):
	"""A form field used for inputting the keywords of a thesis"""
	widget = KeywordWidget

	def to_python(self, value):
		if not value:
			return []

		res = []
		for title in value:
			try:
				k = Keyword.objects.get(title=title)
				res.append(k)
			except Keyword.DoesNotExist:
				raise ValidationError(f"klíčové slovo {title} není v databázi")
		return res


class ThesisKeywordUpdateForm(forms.ModelForm):
	keywords = KeywordUpdateField(label="Klíčová slova", help_text="klíčová slova oddělte čárkami")

	class Meta:
		model = Thesis
		fields = ["keywords"]


class ThesisEvaluationForm(forms.ModelForm):
	state = forms.ModelChoiceField(label="Stav", queryset=models.State.objects.filter(is_closed=True))

	class Meta:
		model = Thesis
		fields = ["mark"]


class SortedModelChoiceIterator(forms.models.ModelChoiceIterator):
	def __iter__(self):
		yield from sorted(super().__iter__(), key=lambda x: "" if not x[0] else x[1])


class SubjectChoiceField(forms.ModelChoiceField):
	iterator = SortedModelChoiceIterator


class ThesisCreateForm(forms.ModelForm):
	subject = SubjectChoiceField(
		label="Předmět",
		queryset=models.Subject.objects.get_queryset(),
	)

	class Meta:
		model = models.Thesis
		fields = ["title", "subject", "assignment"]


class SearchForm(forms.Form):
	title = forms.CharField(required=False, max_length=255, label="Název")
	keywords = KeywordField(required=False, label="Klíčová slova", help_text="klíčová slova oddělte čárkami")
	author_name = forms.CharField(required=False, label="Jméno autora")
	supervisor_name = forms.CharField(required=False, label="Jméno vedoucího")
	opponent_name = forms.CharField(required=False, label="Jméno oponenta")
	year = forms.ChoiceField(required=False, choices=lambda: [(None, "Vše")] + [(y, str(y)) for y in Thesis.public_years()], label="Ročník")
	subject = SubjectChoiceField(
		required=False, empty_label="Vše", label="Předmět",
		queryset=models.Subject.objects.get_queryset(),
	)

	def get_queryset(self):
		qs = Thesis.public.get_queryset()

		if self.cleaned_data["title"]:
			if settings.USE_UNACCENT:
				qs = qs.filter(title__unaccent__icontains=self.cleaned_data["title"])
			else:
				qs = qs.filter(title__icontains=self.cleaned_data["title"])

		if self.cleaned_data["keywords"]:
			for kw in self.cleaned_data["keywords"]:
				qs = qs.filter(keywords=kw)

		if self.cleaned_data["author_name"]:
			first_name, last_name = split_person_name(self.cleaned_data["author_name"])

			if settings.USE_UNACCENT:
				qs = qs.filter(author__last_name__unaccent__iexact=last_name)
			else:
				qs = qs.filter(author__last_name__iexact=last_name)

			if first_name:
				if settings.USE_UNACCENT:
					qs = qs.filter(author__first_name__unaccent__iexact=first_name)
				else:
					qs = qs.filter(author__first_name__iexact=first_name)

		if self.cleaned_data["supervisor_name"]:
			first_name, last_name = split_person_name(self.cleaned_data["supervisor_name"])

			if settings.USE_UNACCENT:
				qs = qs.filter(supervisor__last_name__unaccent__iexact=last_name)
			else:
				qs = qs.filter(supervisor__last_name__iexact=last_name)

			if first_name:
				if settings.USE_UNACCENT:
					qs = qs.filter(supervisor__first_name__unaccent__iexact=first_name)
				else:
					qs = qs.filter(supervisor__first_name__iexact=first_name)

		if self.cleaned_data["opponent_name"]:
			first_name, last_name = split_person_name(self.cleaned_data["opponent_name"])

			if settings.USE_UNACCENT:
				qs = qs.filter(opponent__last_name__unaccent__iexact=last_name)
			else:
				qs = qs.filter(opponent__last_name__iexact=last_name)

			if first_name:
				if settings.USE_UNACCENT:
					qs = qs.filter(opponent__first_name__unaccent__iexact=first_name)
				else:
					qs = qs.filter(opponent__first_name__iexact=first_name)

		if self.cleaned_data["year"]:
			qs = qs.filter(year=self.cleaned_data["year"])

		if self.cleaned_data["subject"]:
			#s = "subject"
			#query = Q(subject=self.cleaned_data["subject"])
			#for _ in range(self.cleaned_data["subject"].maxdepth):
			#	s += "__parent"
			#	query |= Q(**{s: self.cleaned_data["subject"]})
			#qs = qs.filter(query)

			qs = qs.filter(subject__in=self.cleaned_data["subject"].flattree())

		return qs

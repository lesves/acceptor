from django import forms
from .models import Thesis, Keyword, Consultation, ConsultationPeriod
from datetime import date


class ConsultationForm(forms.ModelForm):
	date = forms.DateField(
		initial=date.today, 
		widget=forms.SelectDateWidget(years=range(date.today().year-10, date.today().year+10))
	)

	def __init__(self, *args, **kwargs):
		self.thesis = kwargs.pop("thesis")

		super().__init__(*args, **kwargs)

		self.fields["period"].queryset = self.thesis.subject.inherited_periods()

	class Meta:
		model = Consultation
		fields = ["period", "date"]


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

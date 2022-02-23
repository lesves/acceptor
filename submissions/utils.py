from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class SearchView(ListView):
	"""
		A very simple generic view for displaying search results.

		Require a `form_class` and a `model`. Displays the results 
		of the search form as a `ListView`. The results are retrieved 
		using `SearchView.get_queryset` or using `form_class.get_queryset`.

		Warning: This view has disabled csrf protection.
	"""
	model = None
	form_class = None
	template_name_suffix = "_search"

	def get_queryset(self):
		return self.form.get_queryset()

	def get_context_data(self):
		context = super().get_context_data()
		context["form"] = self.form
		return context

	def get(self, request, *args, **kwargs):
		if request.GET:
			self.form = self.form_class(data=request.GET, initial=request.GET.dict())
		else:
			self.form = self.form_class()

		if self.form.is_valid():
			return super().get(self, request, *args, **kwargs)

		self.object_list = self.model.objects.none()
		context = self.get_context_data()
		return self.render_to_response(context)


def split_person_name(name):
	"""
		A helper function. Split a person name into a first name and a last name.
		Example.
			>>> split_person_name("Filip Oliver Klimoszek")
			("Filip Oliver", "Klimoszek")
			>>> split_person_name("Klimoszek")
			("", "Klimoszek")
	"""
	parts = name.split(" ")
	return " ".join(parts[:-1]), parts[-1]

from django.test import TestCase

from django.core.exceptions import PermissionDenied

from . import models
from .models import Thesis


class ThesisTestCase(TestCase):
	def setUp(self):
		super().setUp()

		self.author = models.User.objects.create(
			username="adam", 
			first_name="Adam", 
			last_name="Smith"
		)
		self.supervisor = models.User.objects.create(
			username="john", 
			first_name="John", 
			last_name="Doe"
		)
		self.subject = models.Subject.objects.create(title="A test subject")

		self.thesis = Thesis.objects.create(
			author=self.author,
			supervisor=self.supervisor,
			title="A test thesis",
			assignment="Some assignment content",
			subject=self.subject,
			year=2018,
		)
		models.LogEntry.objects.create(
			thesis=self.thesis,
			state=models.State.objects.get(code="author_approved"),
			user=self.author,
		)

	#def test_approval(self):

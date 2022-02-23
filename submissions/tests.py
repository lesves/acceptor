from django.test import TestCase

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

import re

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

	def test_approval(self):
		self.thesis.set_state_code("author_approved", self.author)
		self.assertFalse(self.thesis.state.is_approved)

		self.assertRaises(PermissionDenied, self.thesis.approve, self.author)
		self.assertEqual(self.thesis.state.code, "author_approved")
		self.thesis.approve(self.supervisor)
		self.assertEqual(self.thesis.state.code, "approved")

		self.thesis.set_state_code("supervisor_approved", self.supervisor)

		self.assertRaises(PermissionDenied, self.thesis.approve, self.supervisor)
		self.assertEqual(self.thesis.state.code, "supervisor_approved")
		self.thesis.approve(self.author)
		self.assertEqual(self.thesis.state.code, "approved")
		self.assertTrue(self.thesis.state.is_approved)

	def test_submit(self):
		self.thesis.set_state_code("approved", self.supervisor)
		self.assertFalse(self.thesis.state.is_submitted)
		self.thesis.submit()
		self.assertTrue(self.thesis.state.is_submitted)
		self.assertRaises(PermissionDenied, self.thesis.submit)
		self.thesis.cancel_submit()
		self.assertFalse(self.thesis.state.is_submitted)
		self.assertRaises(PermissionDenied, self.thesis.cancel_submit)

		self.thesis.set_state_code("defended", self.supervisor)
		self.assertRaises(PermissionDenied, self.thesis.submit)
		self.assertRaises(PermissionDenied, self.thesis.cancel_submit)


class SystemTestCase(TestCase):
	def setUp(self):
		super().setUp()

		students = Group.objects.get(name="Studenti")
		teachers = Group.objects.get(name="Učitelé")

		author = models.User.objects.create(username="adam", first_name="Adam", last_name="Smith")
		author.set_password("smith")
		author.save()
		students.user_set.add(author)
		students.save()

		supervisor = models.User.objects.create(username="john", first_name="John", last_name="Doe")
		supervisor.set_password("doe")
		supervisor.save()

		opponent = models.User.objects.create(username="lancelot", first_name="Lancelot", last_name="Jones")
		opponent.set_password("jones")
		opponent.save()

		teachers.user_set.add(supervisor)
		teachers.user_set.add(opponent)
		teachers.save()

		subject = models.Subject.objects.create(title="Humanitní studia")
		subsubject = models.Subject.objects.create(title="Filosofie", parent=subject)

	def test_index(self):
		self.assertTemplateUsed(self.client.get("/"), "submissions/index.html")

	def test_create_thesis(self):
		self.client.logout()
		self.assertRedirects(self.client.get("/thesis/create/"), "/auth/login/?next=/thesis/create/")
		self.assertTrue(self.client.login(username="adam", password="smith"))

		self.assertTemplateUsed(self.client.get("/thesis/create/"), "submissions/thesis_form.html")

		res = self.client.post("/thesis/create/")
		self.assertContains(res, "Toto pole je třeba vyplnit.")
		self.assertInHTML('<option value="2">Humanitní studia, Filosofie</option>', res.content.decode())

		res = self.client.post("/thesis/create/", {
				"title": "Testovací práce", 
				"subject": models.Subject.objects.get(title="Filosofie").pk,
				"assignment": "Návrh zadání (verze 1)"})

		thesis = Thesis.objects.get(title="Testovací práce")
		self.assertRedirects(res, f"/thesis/{thesis.pk}/")

		self.assertEqual(thesis.subject.title, "Filosofie")
		self.assertEqual(thesis.state.code, "author_approved")
		self.assertFalse(thesis.state.is_approved)

		return thesis

	def test_subject_thesis_list(self):
		self.client.logout()
		self.assertRedirects(self.client.get("/theses/subject/1/"), "/auth/login/?next=/theses/subject/1/")
		self.assertTrue(self.client.login(username="adam", password="smith"))

		res = self.client.get("/theses/subject/1/")
		self.assertTemplateUsed(res, "submissions/thesis_list.html")

		self.test_create_thesis()

		res = self.client.get("/theses/subject/1/")
		self.assertContains(res, "Testovací práce")

	def test_thesis_detail(self):
		thesis = self.test_create_thesis()

		self.client.logout()
		self.assertRedirects(self.client.get(f"/thesis/{thesis.pk}/"), f"/auth/login/?next=/thesis/{thesis.pk}/")
		self.assertTrue(self.client.login(username="adam", password="smith"))

		self.assertTemplateUsed(self.client.get(f"/thesis/{thesis.pk}/"), "submissions/thesis_detail.html")

	def check_name(self, thesis_pk, role_name, name):
		self.assertIsNotNone(re.search(fr"<th>{role_name}:</th>\s*<td>\s*{name}", self.client.get(f"/thesis/{thesis_pk}/").content.decode()))

	def test_thesis_assign(self):
		thesis = self.test_create_thesis()

		self.client.logout()
		self.assertRedirects(self.client.get("/theses/subject/1/"), "/auth/login/?next=/theses/subject/1/")
		self.assertTrue(self.client.login(username="adam", password="smith"))

		self.assertEquals(self.client.get(f"/thesis/{thesis.pk}/assign/supervisor").status_code, 405)
		self.assertEquals(self.client.post(f"/thesis/{thesis.pk}/assign/supervisor").status_code, 403)

		self.assertTrue(self.client.login(username="john", password="doe"))

		self.check_name(thesis.pk, "Vedoucí", "nepřiřazen")
		self.assertRedirects(self.client.post(f"/thesis/{thesis.pk}/assign/supervisor"), f"/thesis/{thesis.pk}/")
		self.check_name(thesis.pk, "Vedoucí", "John Doe")

		self.assertTrue(self.client.login(username="lancelot", password="jones"))

		self.check_name(thesis.pk, "Oponent", "nepřiřazen")
		self.assertRedirects(self.client.post(f"/thesis/{thesis.pk}/assign/opponent"), f"/thesis/{thesis.pk}/")
		self.check_name(thesis.pk, "Oponent", "Lancelot Jones")

		return thesis

	def test_thesis_approve(self):
		thesis = self.test_thesis_assign()
		thesis_url = f"/thesis/{thesis.pk}/"

		self.assertTrue(self.client.login(username="adam", password="smith"))
		self.assertEquals(self.client.post(f"{thesis_url}approve").status_code, 403)

		self.assertTrue(self.client.login(username="john", password="doe"))

		res = self.client.get(thesis_url)
		self.assertContains(res, "Návrh zadání (verze 1)")
		self.assertContains(res, "Autor schválil")

		self.assertRedirects(
			self.client.post(f"{thesis_url}assignment", {"assignment": "Návrh zadání (verze 2)"}), thesis_url)

		res = self.client.get(thesis_url)
		self.assertContains(res, "Návrh zadání (verze 2)")
		self.assertContains(res, "Vedoucí schválil")

		self.assertTrue(self.client.login(username="adam", password="smith"))
		self.assertRedirects(self.client.post(f"{thesis_url}approve"), thesis_url)

		thesis.refresh_from_db()
		self.assertTrue(thesis.state.is_approved)

		self.assertEquals(self.client.post(f"{thesis_url}approve").status_code, 403)

		return thesis

	def test_thesis_submit(self):
		thesis = self.test_thesis_approve()
		thesis_url = f"/thesis/{thesis.pk}/"

		self.assertTrue(self.client.login(username="adam", password="smith"))

		self.assertContains(self.client.post(f"{thesis_url}attachment/link", {"url": "abc"}), "Zadejte platnou adresu URL.")
		self.assertRedirects(self.client.post(f"{thesis_url}attachment/link", {"url": "https://example.com"}), thesis_url)

		self.assertContains(self.client.get(thesis_url), "https://example.com")
		self.assertRedirects(self.client.post(f"{thesis_url}attachment/{thesis.attachments.first().pk}/delete"), thesis_url)

		self.assertRedirects(self.client.post(f"{thesis_url}attachment/link", {"url": "https://example.org"}), thesis_url)

		res = self.client.get(thesis_url)
		self.assertNotContains(res, "https://example.com")
		self.assertContains(res, "https://example.org")

		self.assertEquals(self.client.post(f"{thesis_url}submit-cancel").status_code, 403)
		self.assertRedirects(self.client.post(f"{thesis_url}submit"), thesis_url)
		self.assertRedirects(self.client.post(f"{thesis_url}submit-cancel"), thesis_url)
		self.assertRedirects(self.client.post(f"{thesis_url}submit"), thesis_url)

		self.assertEquals(self.client.post(f"{thesis_url}attachment/link", {"url": "https://example.com"}).status_code, 403)
		self.assertEquals(self.client.post(f"{thesis_url}attachment/{thesis.attachments.first().pk}/delete").status_code, 403)

		thesis.refresh_from_db()
		self.assertTrue(thesis.state.is_submitted)

		return thesis

	def test_thesis_opinions(self):
		thesis = self.test_thesis_submit()
		thesis_url = f"/thesis/{thesis.pk}/"
		self.assertFalse(thesis.state.code == "defense_ready")

		self.assertTrue(self.client.login(username="adam", password="smith"))
		self.assertEquals(self.client.post(f"{thesis_url}opinion/supervisor/update", {"supervisor_opinion": "skvělé"}).status_code, 403)
		self.assertEquals(self.client.get(f"{thesis_url}opinion/supervisor/").status_code, 404)

		self.assertTrue(self.client.login(username="john", password="doe"))
		self.assertRedirects(self.client.post(f"{thesis_url}opinion/supervisor/update", {"supervisor_opinion": "skvělé"}), thesis_url)
		self.assertContains(self.client.get(f"{thesis_url}opinion/supervisor/"), "skvělé")
		
		thesis.refresh_from_db()
		self.assertFalse(thesis.state.code == "defense_ready")

		self.assertTrue(self.client.login(username="lancelot", password="jones"))
		self.assertRedirects(self.client.post(f"{thesis_url}opinion/opponent/update", {"opponent_opinion": "strašné"}), thesis_url)
		self.assertContains(self.client.get(f"{thesis_url}opinion/opponent/"), "strašné")

		thesis.refresh_from_db()
		self.assertTrue(thesis.state.code == "defense_ready")

		return thesis

	def test_thesis_evaluation(self):
		thesis = self.test_thesis_opinions()
		thesis_url = f"/thesis/{thesis.pk}/"

		self.assertEquals(thesis.mark, None)

		self.client.login(username="adam", password="smith")
		self.assertEquals(403, self.client.post(f"{thesis_url}state", {"state": "postponed"}).status_code)

		self.client.login(username="john", password="doe")
		self.assertRedirects(self.client.post(f"{thesis_url}state", {"state": "postponed"}), thesis_url)
		thesis.refresh_from_db()

		self.assertEquals(thesis.state.code, "postponed")
		self.assertEquals(thesis.mark, None)

		self.client.login(username="adam", password="smith")
		self.assertEquals(403, self.client.post(f"{thesis_url}evaluation", {"mark": "1"}).status_code)

		self.client.login(username="john", password="doe")
		self.assertRedirects(self.client.post(f"{thesis_url}evaluation", {"mark": "1"}), thesis_url)

		thesis.refresh_from_db()
		self.assertEquals(thesis.mark, 1)
		self.assertEquals(thesis.state.code, "defended")

		return thesis

	def test_archive(self):
		thesis = self.test_thesis_evaluation()

		self.assertContains(self.client.get("/archive/"), str(thesis.year))
		self.assertContains(self.client.get(f"/archive/search/?year={thesis.year}"), thesis.title)


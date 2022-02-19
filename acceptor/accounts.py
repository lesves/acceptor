from django.conf import settings
from django.contrib.auth.models import Group

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SubmissionAccountAdapter(DefaultSocialAccountAdapter):
	"""
	Prevent Google logins from accounts outside `settings.EMAIL_DOMAIN`
	and set the username of new users according to their gmail.
	"""

	def is_open_for_signup(self, request, socialaccount):
		if not socialaccount.email_addresses:
			return False
		return socialaccount.email_addresses[0].email.endswith("@" + settings.EMAIL_DOMAIN)

	def populate_user(self, request, sociallogin, data):
		user = super().populate_user(request, sociallogin, data)
		user.username = user.email[:-(len(settings.EMAIL_DOMAIN)+1)]
		
		return user

	def save_user(self, request, sociallogin, form):
		super().save_user(request, sociallogin, form)

		if settings.IS_STUDENT_USERNAME(sociallogin.account.user.username):
			group = Group.objects.get(name="Studenti")
		else:
			group = Group.objects.get(name="Učitelé")
		group.user_set.add(sociallogin.account.user)
		group.save()
		sociallogin.account.user.save()

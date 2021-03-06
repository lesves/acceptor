from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django_q.tasks import async_task

from .models import Thesis, ConsultationPeriod, Consultation, User
from datetime import date


def notify(email, thesis, have, required, remaining_days):
	send_mail(
		settings.CONSULTATION_EMAIL_SUBJECT,
		render_to_string("submissions/emails/consultation.txt", {"thesis": thesis, "required": required, "have": have, "remaining_days": remaining_days}),
		None,
		[email],
		fail_silently=False,
	)


def notifications(remaining=settings.CONSULTATION_EMAIL_DAYS_LEFT):
	today = date.today()
	for period in ConsultationPeriod.objects.all():
		delta = period.end-today

		to_notify = []
		if delta.days == remaining:
			for thesis in Thesis.not_closed.all():
				cons = thesis.periods().get(period)
				if cons is None:
					continue

				if cons.count() < period.count:
					if thesis.author and thesis.author.email:
						async_task("submissions.tasks.notify", thesis.author.email, thesis, cons.count(), period.count, remaining)

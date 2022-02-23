from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
	help = "Sets up a scheduled task for sending emails"

	def handle(self, *args, **options):
		if not Schedule.objects.filter(func="submissions.tasks.notifications").exists():
			Schedule.objects.create(
				func="submissions.tasks.notifications",
				schedule_type=Schedule.DAILY,
			)

		self.stdout.write(self.style.SUCCESS("Successfully set the scheduled task."))

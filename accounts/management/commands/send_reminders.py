from django.core.management.base import BaseCommand
from accounts.integrations import CalendarReminderService


class Command(BaseCommand):
    help = 'Send appointment reminders to users'

    def handle(self, *args, **options):
        self.stdout.write('Sending appointment reminders...')

        reminder_count = CalendarReminderService.send_reminders()

        if reminder_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Sent {reminder_count} appointment reminders.')
            )
        else:
            self.stdout.write('No reminders to send.')
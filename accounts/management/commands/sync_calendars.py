from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CalendarIntegration
from accounts.integrations import GoogleCalendarService


class Command(BaseCommand):
    help = 'Sync all user calendars with Google Calendar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sync calendar for specific user ID only',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting calendar sync...')

        # Get calendar integrations to sync
        if options['user_id']:
            integrations = CalendarIntegration.objects.filter(
                user_id=options['user_id'],
                is_connected=True,
                sync_enabled=True
            )
        else:
            integrations = CalendarIntegration.objects.filter(
                is_connected=True,
                sync_enabled=True
            )

        total_synced = 0
        total_integrations = integrations.count()

        for integration in integrations:
            try:
                service = GoogleCalendarService(integration)
                synced_count = service.sync_appointments()

                if synced_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Synced {synced_count} appointments for user {integration.user.username}'
                        )
                    )
                    total_synced += synced_count
                else:
                    self.stdout.write(
                        f'No new appointments to sync for user {integration.user.username}'
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error syncing calendar for user {integration.user.username}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Calendar sync completed. Synced {total_synced} appointments across {total_integrations} integrations.'
            )
        )
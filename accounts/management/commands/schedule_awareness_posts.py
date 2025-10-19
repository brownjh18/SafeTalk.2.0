from django.core.management.base import BaseCommand
from accounts.models import User
from accounts.social_integrations import MentalHealthContentScheduler


class Command(BaseCommand):
    help = 'Schedule mental health awareness posts for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Schedule posts for specific user ID only',
        )

    def handle(self, *args, **options):
        self.stdout.write('Scheduling mental health awareness posts...')

        # Get users to schedule posts for
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                users = [user]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found.')
                )
                return
        else:
            users = User.objects.filter(is_active=True)

        total_scheduled = 0
        processed_users = 0

        for user in users:
            try:
                scheduler = MentalHealthContentScheduler()
                scheduled_count = scheduler.schedule_weekly_awareness_posts(user)

                if scheduled_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Scheduled {scheduled_count} awareness posts for user {user.username}'
                        )
                    )
                    total_scheduled += scheduled_count
                else:
                    self.stdout.write(
                        f'No posts scheduled for user {user.username} (social sharing disabled or no platforms connected)'
                    )

                processed_users += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error scheduling posts for user {user.username}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Awareness post scheduling completed. Scheduled {total_scheduled} posts for {processed_users} users.'
            )
        )
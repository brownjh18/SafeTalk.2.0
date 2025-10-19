from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from analytics.services import AnalyticsService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Update analytics for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Update analytics for specific user (username)',
        )
        parser.add_argument(
            '--risk-assessment',
            action='store_true',
            help='Perform risk assessments for high-risk users',
        )
        parser.add_argument(
            '--generate-reports',
            action='store_true',
            help='Generate weekly reports for users',
        )

    def handle(self, *args, **options):
        if options['user']:
            # Update analytics for specific user
            try:
                user = User.objects.get(username=options['user'])
                self.stdout.write(f'Updating analytics for user: {user.username}')

                analytics = AnalyticsService.update_user_analytics(user)
                if analytics:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully updated analytics for {user.username}: '
                            f'Engagement={analytics.engagement_score:.1f}, '
                            f'Risk={analytics.risk_score:.1f}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to update analytics for {user.username}')
                    )

            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{options["user"]}" not found')
                )

        elif options['risk_assessment']:
            # Perform risk assessments
            self.stdout.write('Performing risk assessments for high-risk users...')
            from analytics.signals import perform_risk_assessments
            perform_risk_assessments()
            self.stdout.write(self.style.SUCCESS('Risk assessments completed'))

        elif options['generate_reports']:
            # Generate reports
            self.stdout.write('Generating weekly reports...')
            from analytics.signals import generate_weekly_reports
            generate_weekly_reports()
            self.stdout.write(self.style.SUCCESS('Report generation completed'))

        else:
            # Update analytics for all users
            self.stdout.write('Updating analytics for all users...')

            users = User.objects.all()
            success_count = 0
            error_count = 0

            for user in users:
                try:
                    analytics = AnalyticsService.update_user_analytics(user)
                    if analytics:
                        success_count += 1
                        if success_count % 10 == 0:  # Progress update every 10 users
                            self.stdout.write(f'Processed {success_count} users...')
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f'Error updating analytics for user {user.id}: {str(e)}')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Analytics update completed: {success_count} successful, {error_count} errors'
                )
            )
from django.core.management.base import BaseCommand
from accounts.social_integrations import SocialMediaScheduler


class Command(BaseCommand):
    help = 'Process scheduled social media posts'

    def handle(self, *args, **options):
        self.stdout.write('Processing scheduled social media posts...')

        processed_count = SocialMediaScheduler.process_scheduled_posts()

        if processed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Processed {processed_count} scheduled posts.')
            )
        else:
            self.stdout.write('No posts to process.')
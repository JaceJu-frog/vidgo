from django.core.management.base import BaseCommand
from video.models import Video

class Command(BaseCommand):
    help = 'Removes media/saved_video/ prefix from video URLs'

    def handle(self, *args, **options):
        # Find videos with the prefix we want to remove
        videos = Video.objects.filter(url__contains='media/saved_video/').filter(url__endswith='.mp4')
        self.stdout.write(f'Found {videos.count()} videos with media/saved_video/ prefix')

        # Update each video's URL
        updated = 0
        for video in videos:
            old_url = video.url
            new_url = video.url.replace('media/saved_video/', '')
            video.url = new_url
            video.save()
            self.stdout.write(f'Updated: {old_url} -> {new_url}')
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} video URLs'))

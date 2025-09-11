from django.core.management.base import BaseCommand
from django.conf import settings
from video.models import Video
import ffmpeg
import os


class Command(BaseCommand):
    help = 'Updates video_length field for all videos in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update videos even if they already have a length set'
        )

    def get_video_duration(self, file_path):
        """使用ffmpeg获取视频时长(秒)"""
        if not os.path.exists(file_path):
            return None
            
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Failed to get duration for {file_path}: {str(e)}")
            )
            return None

    def format_duration(self, seconds):
        """将秒数转换为 HH:MM:SS 格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # 获取需要更新的视频
        if force:
            videos = Video.objects.filter(url__isnull=False).exclude(url='')
            self.stdout.write(f'Found {videos.count()} videos to update (force mode)')
        else:
            videos = Video.objects.filter(
                url__isnull=False,
                video_length__isnull=True
            ).exclude(url='')
            self.stdout.write(f'Found {videos.count()} videos without length info')

        if videos.count() == 0:
            self.stdout.write(self.style.SUCCESS('No videos need updating'))
            return

        updated_count = 0
        error_count = 0
        
        for video in videos:
            # 构建完整文件路径
            video_path = os.path.join(settings.MEDIA_ROOT, 'saved_video', video.url)
            
            if dry_run:
                self.stdout.write(f'Would process: {video.name} ({video_path})')
                continue
                
            # 获取视频时长
            duration = self.get_video_duration(video_path)
            
            if duration is not None:
                formatted_duration = self.format_duration(duration)
                video.video_length = formatted_duration
                video.save(update_fields=['video_length'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {video.name} (ID: {video.id}): {formatted_duration}'
                    )
                )
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to get duration for {video.name} (ID: {video.id})'
                    )
                )
                error_count += 1

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run completed - no changes made'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} videos. '
                    f'{error_count} errors occurred.'
                )
            )
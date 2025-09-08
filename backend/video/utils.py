from django.utils import timezone
from django.conf import settings
import ffmpeg
import os

def get_video_duration(file_path):
    """使用ffmpeg获取视频时长(秒)"""
    if not os.path.exists(file_path):
        return None
        
    try:
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"Failed to get duration for {file_path}: {str(e)}")
        return None

def format_duration(seconds):
    """将秒数转换为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def update_video_length(video):
    """更新单个视频的时长信息"""
    if not video.url:
        return None
        
    video_path = os.path.join(settings.MEDIA_ROOT, 'saved_video', video.url)
    duration = get_video_duration(video_path)
    
    if duration is not None:
        formatted_duration = format_duration(duration)
        video.video_length = formatted_duration
        video.save(update_fields=['video_length'])
        return formatted_duration
    return None

def calc_diff_time(start_time):
    #计算视频最后一次打开时间与当前时间的差值。
    # 并按照分钟为单位，如果小于1分钟，返回一分钟内；小于1小时返回一小时内；小于1天返回一天内
    # 否则返回大于1天
    now = timezone.now()
    diff = now - start_time
    if diff.total_seconds() < 60:
        return "一分钟内"
    elif diff.total_seconds() < 3600:
        return "一小时内"
    elif diff.total_seconds() < 86400:
        return "一天内"
    elif diff.total_seconds() < 86400*7:
        days= diff.days
        return f"{days}天内"
    else:
        return "大于一周"
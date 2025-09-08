# update_video_durations.py

from vid_go.video.app import app, db
from vid_go.video.models import Video
import os
from moviepy.editor import VideoFileClip

def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

def update_video_lengths():
    with app.app_context():
        videos = Video.query.all()
        for video in videos:
            relative_path = video.url  # Assuming this is the relative path
            if not relative_path:
                print(f"No path for video {video.name}")
                continue

            # Construct the absolute path
            # Assuming the videos are stored relative to a base directory
            base_directory = os.path.abspath('/media/jju/ExtraDisk1/Downloads/ui_for_whisper/whisper-my/')
            absolute_path = os.path.join(base_directory, relative_path)

            if os.path.exists(absolute_path):
                try:
                    clip = VideoFileClip(absolute_path)
                    duration = clip.duration  # Duration in seconds
                    formatted_duration = format_duration(duration)
                    video.video_length = formatted_duration
                    db.session.add(video)
                    print(f"Updated {video.name} with duration {formatted_duration}")
                except Exception as e:
                    print(f"Error processing {video.name}: {e}")
            else:
                print(f"File not found: {absolute_path}")

        db.session.commit()
        print("Video lengths updated.")

if __name__ == "__main__":
    update_video_lengths()

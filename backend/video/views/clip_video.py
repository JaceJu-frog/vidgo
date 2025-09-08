def clip_video(request):
    data = request.get_json()
    video_id = data.get('video_id')
    srt_content = data.get('srt_content')
    sid = data.get('sid')  # 客户端的 Socket.IO 会话 ID
    task_id = data.get('task_id')  # 任务的唯一标识

    # Validate inputs
    if not video_id or not srt_content or not sid or not task_id:
        return JsonResponse({'success': False, 'message': 'Invalid input'}), 400

    # Fetch video from the database
    video = Video.query.get(video_id)
    if not video:
        return JsonResponse({'success': False, 'message': f"Video with ID {video_id} not found."}), 404

    video_path = video.url
    if not os.path.exists(video_path):
        return JsonResponse({'success': False, 'message': f"Video file {video_path} not found."}), 404

    # Parse srt_content and build FFmpeg command
    timestamps = []
    lines = srt_content.strip().splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.isdigit():
            # Skip subtitle number
            index += 1
            if index < len(lines):
                time_line = lines[index].strip()
                if '-->' in time_line:
                    start_time_str, end_time_str = time_line.split('-->')
                    start_time = srt_time_to_seconds(start_time_str)
                    end_time = srt_time_to_seconds(end_time_str)
                    timestamps.append((start_time, end_time))
                    index += 1
                else:
                    index += 1
            else:
                break
        else:
            index += 1

    if not timestamps:
        print("No valid timestamps found in the SRT content.")
        return JsonResponse({'success': False, 'message': "No valid timestamps found in the SRT content."}), 400

    # Build FFmpeg's filter_complex parameter
    filter_complex_parts = []
    concat_inputs = ''
    for i, (start, end) in enumerate(timestamps):
        filter_complex_parts.append(
            f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];"
        )
        concat_inputs += f"[v{i}][a{i}]"

    filter_complex = ''.join(filter_complex_parts)
    filter_complex += f"{concat_inputs}concat=n={len(timestamps)}:v=1:a=1[outv][outa]"

    temp_output = f'temp_output_{task_id}.mp4'

    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        '-map', '[outa]',
        '-progress', 'pipe:1',
        '-nostats',
        '-y',
        temp_output
    ]

    threading.Thread(target=run_ffmpeg, args=(cmd, sid, task_id, video_id, temp_output, timestamps)).start()
    return JsonResponse({'success': True, 'message': 'Video processing started.'})

import hashlib
import os

def parse_ffmpeg_time(time_str):
    """
    Parse 'HH:MM:SS.micros' format to total seconds.
    """
    if '.' in time_str:
        hms, micros = time_str.split('.')
        micros = float('0.' + micros)
    else:
        hms = time_str
        micros = 0
    hours, minutes, seconds = map(float, hms.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds + micros
    return total_seconds

# def run_ffmpeg(cmd, sid, task_id, video_id, temp_output, timestamps):
#     """
#     执行 FFmpeg 命令并通过 Socket.IO 向客户端发送进度更新。
#     """
#     with app.app_context():
#         total_duration = sum(end - start for start, end in timestamps)
#         video = Video.query.get(video_id)
#         process = subprocess.Popen(
#             cmd,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT,  # Combine stdout and stderr
#             universal_newlines=True,
#             bufsize=1
#         )

#         for line in process.stdout:
#             line = line.strip()
#             if line:
#                 if 'out_time=' in line:
#                     # Extract the out_time value
#                     try:
#                         time_str = line.split('out_time=')[1].split(' ')[0]
#                         progress_time = parse_ffmpeg_time(time_str)
#                         progress_percentage = min((progress_time / total_duration) * 100, 100)
#                         # Emit progress update to the client
#                         socketio.emit(
#                             'ffmpeg_progress',
#                             {'task_id': task_id, 'progress': progress_percentage},
#                             room=sid
#                         )
#                         print(f'Task {task_id} Progress: {progress_percentage:.2f}%')
#                     except (IndexError, ValueError) as e:
#                         print(f"Error parsing FFmpeg output: {e}")

#         process.stdout.close()
#         process.wait()

#         if process.returncode != 0:
#             # Emit error event to the client
#             socketio.emit(
#                 'ffmpeg_error',
#                 {'task_id': task_id, 'message': 'FFmpeg processing failed.'},
#                 room=sid
#             )
#             print(f"Task {task_id} Failed.")
#             return

#         # Calculate MD5 hash of the new video file
#         try:
#             md5_hash = hashlib.md5()
#             with open(temp_output, 'rb') as f:
#                 for chunk in iter(lambda: f.read(4096), b''):
#                     md5_hash.update(chunk)
#             md5_value = md5_hash.hexdigest()
#         except FileNotFoundError:
#             socketio.emit(
#                 'ffmpeg_error',
#                 {'task_id': task_id, 'message': 'Temporary output file not found.'},
#                 room=sid
#             )
#             print(f"Task {task_id} Temporary output file not found.")
#             return

#         # Create directory to save the new video
#         save_dir = 'media/saved_video'
#         os.makedirs(save_dir, exist_ok=True)

#         # New video file path
#         new_video_filename = f"{md5_value}.mp4"
#         new_video_path = os.path.join(save_dir, new_video_filename)

#         # Move and rename the temporary output file
#         try:
#             os.replace(temp_output, new_video_path)
#         except OSError as e:
#             socketio.emit(
#                 'ffmpeg_error',
#                 {'task_id': task_id, 'message': f'Failed to move output file: {e}'},
#                 room=sid
#             )
#             print(f"Task {task_id} Failed to move output file: {e}")
#             return

#         # Update the video's URL in the database
#         video.url = new_video_path  # Update to the new relative path
#         print("现在的视频链接",video.url)
#         # print("",video.)
#         # Here you should also update any other fields if necessary (e.g., MD5)
#         # Example: video.md5 = md5_value

#         # Commit database changes
#         # Assuming you have a database session (replace with actual DB code)
#         # db.session.commit()

#         print(f"Task {task_id}: Video has been clipped and saved to {new_video_path}. Database updated.")

#         # Emit completion message to the client
#         socketio.emit(
#             'ffmpeg_complete',
#             {'task_id': task_id, 'message': 'Video has been clipped and saved.'},
#             room=sid
#         )
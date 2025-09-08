"""
Views for standalone audio/HLS conversion endpoints.
"""
import os

from django.http import JsonResponse, HttpRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from ..services.audio_processing import (
    get_video_file_paths,
    detect_video_audio_format,
    extract_audio_from_video_file,
    extract_hls_from_video_file,
)
from ..models import Video


@method_decorator(csrf_exempt, name='dispatch')
class ConvertAudioView(View):
    """Convert a video file to audio (delete original video) and update the database."""
    http_method_names = ['post']

    def post(self, request: HttpRequest, video_id: int, *args, **kwargs):
        video, video_path, audio_dir = get_video_file_paths(video_id)
        os.makedirs(audio_dir, exist_ok=True)

        base, _ = os.path.splitext(video.url)
        audio_ext = detect_video_audio_format(video_path)
        audio_filename = f"{base}.{audio_ext}"
        audio_path = os.path.join(audio_dir, audio_filename)

        success, err_msg, _ = extract_audio_from_video_file(
            video_path, audio_path, preserve_format=True
        )
        if not success:
            return JsonResponse(
                {'success': False, 'error': err_msg or 'Audio extraction failed'},
                status=500,
            )

        try:
            os.remove(video_path)
        except OSError:
            pass

        video.url = audio_filename
        video.video_length = ''
        video.save(update_fields=['url', 'video_length'])
        return JsonResponse({'success': True, 'audio': audio_filename})


@method_decorator(csrf_exempt, name='dispatch')
class ConvertHLSView(View):
    """Convert a video file to HLS (m3u8+ts) and update the DB with HLS path."""
    http_method_names = ['post']

    def post(self, request: HttpRequest, video_id: int, *args, **kwargs):
        video = get_object_or_404(Video, pk=video_id)
        _, video_path, _ = get_video_file_paths(video_id)

        ok, err, rel_dir = extract_hls_from_video_file(video_path)
        if not ok:
            return JsonResponse(
                {'success': False, 'error': err or 'HLS conversion failed'},
                status=500,
            )

        video.save(update_fields=['url'])
        return JsonResponse({'success': True, 'hls_path': rel_dir})

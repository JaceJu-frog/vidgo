from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from ..models import Video
from .videos import is_audio_file, get_media_path_info
import os
import subprocess
import tempfile


@method_decorator(csrf_exempt, name='dispatch')
class VideoDownloadView(View):
    """Stream video/audio files for download with progress support using StreamingHttpResponse"""
    http_method_names = ['get', 'head']

    def get_file_info(self, video_id: int, format_type: str):
        """Get file path and validate format using existing helper functions"""
        try:
            video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            return None, None, "视频不存在"

        if not video.url:
            return None, None, "视频文件路径为空"

        # Use existing helper function to get media directory
        directory_name, _ = get_media_path_info(video.url)
        file_path = os.path.join(settings.MEDIA_ROOT, directory_name, video.url)
        
        if format_type == 'mp4':
            # Check if it's already a video file
            if not is_audio_file(video.url):
                if os.path.exists(file_path):
                    return file_path, video.url, None
                else:
                    return None, None, "MP4文件不存在"
            else:
                return None, None, "音频文件无法导出为MP4格式，请选择MP3"
                
        elif format_type == 'mp3':
            # If it's already an audio file
            if is_audio_file(video.url):
                if os.path.exists(file_path):
                    return file_path, video.url, None
                else:
                    return None, None, "MP3文件不存在"
            else:
                # It's a video file, check if it exists for audio extraction
                if os.path.exists(file_path):
                    return file_path, video.url, None
                else:
                    return None, None, "视频文件不存在，无法提取音频"
        
        return None, None, "不支持的格式"

    def head(self, request, video_id: int, format_type: str):
        """Handle HEAD request to check file availability and size"""
        file_path, filename, error = self.get_file_info(video_id, format_type)
        
        if error:
            if "音频文件无法导出为MP4" in error:
                return HttpResponse(status=400)  # Bad Request
            return HttpResponse(status=404)  # Not Found
        
        if not file_path or not os.path.exists(file_path):
            return HttpResponse(status=404)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Set appropriate content type
        content_type = 'video/mp4' if format_type == 'mp4' else 'audio/mpeg'
        
        response = HttpResponse(status=200)
        response['Content-Length'] = str(file_size)
        response['Content-Type'] = content_type
        response['Accept-Ranges'] = 'bytes'
        return response

    def get(self, request, video_id: int, format_type: str):
        """Stream file download with chunked response using StreamingHttpResponse"""
        from django.http import StreamingHttpResponse
        
        file_path, filename, error = self.get_file_info(video_id, format_type)
        
        if error:
            if "音频文件无法导出为MP4" in error:
                return JsonResponse({'error': error}, status=400)
            return JsonResponse({'error': error}, status=404)
        
        if not file_path or not os.path.exists(file_path):
            return JsonResponse({'error': '文件不存在'}, status=404)
        
        # For MP3 format from video file, we need to extract audio
        if format_type == 'mp3' and not is_audio_file(filename):
            return self.stream_extracted_audio(file_path, filename)
        
        # Direct file streaming
        return self.stream_file(file_path, filename, format_type)

    def stream_file(self, file_path: str, filename: str, format_type: str):
        """Stream file directly with StreamingHttpResponse for memory efficiency"""
        from django.http import StreamingHttpResponse
        
        file_size = os.path.getsize(file_path)
        content_type = 'video/mp4' if format_type == 'mp4' else 'audio/mpeg'
        
        def file_iterator(chunk_size=8192):
            """Generator that yields file chunks without loading entire file into memory"""
            try:
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            except IOError as e:
                print(f"Error reading file {file_path}: {e}")
                yield b''
        
        response = StreamingHttpResponse(
            file_iterator(),
            content_type=content_type
        )
        response['Content-Length'] = str(file_size)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'no-cache'
        return response

    def stream_extracted_audio(self, video_path: str, original_filename: str):
        """Extract audio from video and stream as MP3 using StreamingHttpResponse"""
        from django.http import StreamingHttpResponse
        
        # Create temporary file for extracted audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_audio_path = temp_file.name
        
        try:
            # Extract audio using ffmpeg
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'mp3',
                '-ab', '192k',  # Audio bitrate
                '-y',  # Overwrite output file
                temp_audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                return JsonResponse({'error': '音频提取失败'}, status=500)
            
            # Stream the extracted audio
            file_size = os.path.getsize(temp_audio_path)
            
            def audio_iterator(chunk_size=8192):
                """Generator for streaming extracted audio without memory overhead"""
                try:
                    with open(temp_audio_path, 'rb') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk
                except IOError as e:
                    print(f"Error reading extracted audio {temp_audio_path}: {e}")
                    yield b''
                finally:
                    # Clean up temporary file after streaming
                    try:
                        os.unlink(temp_audio_path)
                    except Exception as e:
                        print(f"Error cleaning up temp file {temp_audio_path}: {e}")
            
            # Generate appropriate filename for MP3
            mp3_filename = os.path.splitext(original_filename)[0] + '.mp3'
            
            response = StreamingHttpResponse(
                audio_iterator(),
                content_type='audio/mpeg'
            )
            response['Content-Length'] = str(file_size)
            response['Content-Disposition'] = f'attachment; filename="{mp3_filename}"'
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache'
            return response
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_audio_path)
            except:
                pass
            return JsonResponse({'error': f'音频提取异常: {str(e)}'}, status=500)
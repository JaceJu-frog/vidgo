from django.views import View
from django.http import JsonResponse, StreamingHttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import uuid
import time
import os
import mimetypes
from ..tasks import export_queue, export_task_status, export_update_status
from ..models import Video

@method_decorator(csrf_exempt, name='dispatch')
class ExportTaskAddView(View):
    """Add video export task"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            video_id = data.get('video_id')
            subtitle_type = data.get('subtitle_type', 'raw')  # raw, translated, both
            
            if not video_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Missing video ID'
                })
            
            # Check if video exists
            try:
                video = Video.objects.get(pk=video_id)
            except Video.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Video does not exist'
                })
            
            # Check if subtitle files exist
            if subtitle_type in ['raw', 'both'] and not video.srt_path:
                return JsonResponse({
                    'success': False,
                    'message': 'This video has no raw subtitle file'
                })
            
            if subtitle_type in ['translated', 'both'] and not video.translated_srt_path:
                return JsonResponse({
                    'success': False,
                    'message': 'This video has no translated subtitle file'
                })
            
            # Generate task ID
            task_id = f"export_{video_id}_{int(time.time())}"
            
            # Initialize task status
            export_task_status[task_id].update({
                "video_id": video_id,
                "video_name": video.name,
                "subtitle_type": subtitle_type,
                "status": "Queued",
                "progress": 0,
                "output_filename": "",
                "error_message": "",
            })
            
            # Add to queue
            export_queue.put(task_id)
            
            return JsonResponse({
                'success': True,
                'message': 'Export task added to queue',
                'task_id': task_id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Server error: {str(e)}'
            })

class AllExportStatusView(View):
    """Get all export task statuses"""
    
    def get(self, request):
        return JsonResponse({
            'success': True,
            'data': dict(export_task_status)
        })

class ExportStatusView(View):
    """Get single export task status"""
    
    def get(self, request, task_id):
        if task_id not in export_task_status:
            return JsonResponse({
                'success': False,
                'message': 'Task does not exist'
            })
        
        return JsonResponse({
            'success': True,
            'data': export_task_status[task_id]
        })

@method_decorator(csrf_exempt, name='dispatch')
class DeleteExportTaskView(View):
    """Delete export task"""
    
    def delete(self, request, task_id):
        if task_id not in export_task_status:
            return JsonResponse({
                'success': False,
                'message': 'Task does not exist'
            })
        
        task = export_task_status[task_id]
        
        # Delete output file (if exists)
        import os
        if task['output_filename']:
            output_path = os.path.join('work_dir/export_videos', task['output_filename'])
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception as e:
                print(f"Failed to delete export file: {e}")
        
        # Delete from task status
        del export_task_status[task_id]
        
        return JsonResponse({
            'success': True,
            'message': 'Task deleted'
        })

@method_decorator(csrf_exempt, name='dispatch')
class RetryExportTaskView(View):
    """Retry export task"""
    
    def post(self, request, task_id):
        if task_id not in export_task_status:
            return JsonResponse({
                'success': False,
                'message': 'Task does not exist'
            })
        
        task = export_task_status[task_id]
        
        # Reset task status
        export_update_status(task_id, "Queued", 0, "")
        task['output_filename'] = ""
        
        # Re-add to queue
        export_queue.put(task_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Task re-added to queue'
        })

class ExportedVideoDownloadView(View):
    """Download exported video file"""
    
    def get(self, request, task_id):
        if task_id not in export_task_status:
            raise Http404("Task does not exist")
        
        task = export_task_status[task_id]
        
        # Check task status and output file
        if task['status'] != 'Completed' or not task['output_filename']:
            raise Http404("File not available")
        
        # Build file path
        export_dir = 'work_dir/export_videos'
        file_path = os.path.join(export_dir, task['output_filename'])
        
        if not os.path.exists(file_path):
            raise Http404("File does not exist")
        
        # Get file information
        file_size = os.path.getsize(file_path)
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'video/mp4'
        
        # Handle Range requests (for supporting resume and video player seek)
        range_header = request.headers.get('Range')
        if range_header:
            import re
            # Parse Range request header
            range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                
                if end >= file_size:
                    end = file_size - 1
                
                length = end - start + 1
                
                # Create partial response
                def file_iterator(file_path, start, length, chunk_size=8192):
                    with open(file_path, 'rb') as f:
                        f.seek(start)
                        remaining = length
                        while remaining > 0:
                            chunk_size = min(chunk_size, remaining)
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                
                response = StreamingHttpResponse(
                    file_iterator(file_path, start, length),
                    status=206,  # Partial Content
                    content_type=content_type
                )
                response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                response['Content-Length'] = str(length)
                response['Accept-Ranges'] = 'bytes'
                
                return response
        
        # Normal complete file download
        def file_iterator(file_path, chunk_size=8192):
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        
        response = StreamingHttpResponse(
            file_iterator(file_path),
            content_type=content_type
        )
        
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        
        return response
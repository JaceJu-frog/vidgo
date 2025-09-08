"""
External Transcription API Views
Handles MP3 file uploads from other VidGo instances or external services
for whisper transcription service
"""
import os
import uuid
import time
import json
import requests
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from ..tasks import external_task_status, subtitle_task_queue


@method_decorator(csrf_exempt, name='dispatch')
class ExternalTranscriptionSubmitView(View):
    """
    Submit MP3 file for transcription
    Supports both file upload and URL download
    """
    http_method_names = ["post"]
    
    def post(self, request):
        try:
            # Parse request data
            if request.content_type and request.content_type.startswith('application/json'):
                data = json.loads(request.body)
                source_type = "url"
                audio_url = data.get('audio_url')
                if not audio_url:
                    return JsonResponse({
                        'error': 'audio_url is required for JSON requests'
                    }, status=400)
                filename = data.get('filename', f'audio_{int(time.time())}.mp3')
            else:
                # File upload
                source_type = "upload"
                if 'audio_file' not in request.FILES:
                    return JsonResponse({
                        'error': 'audio_file is required for file uploads'
                    }, status=400)
                
                audio_file = request.FILES['audio_file']
                filename = audio_file.name
                
                # Validate file type
                allowed_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in allowed_extensions:
                    return JsonResponse({
                        'error': f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'
                    }, status=400)
            
            # Generate unique task ID with 'ext_' prefix
            task_id = f'ext_{str(uuid.uuid4())}'
            
            # Create external transcription work directory
            external_audio_dir = 'work_dir/external_audio'
            os.makedirs(external_audio_dir, exist_ok=True)
            
            # Save file path
            file_path = os.path.join(external_audio_dir, f"{task_id}_{filename}")
            
            if source_type == "upload":
                # Save uploaded file
                with open(file_path, 'wb+') as destination:
                    for chunk in audio_file.chunks():
                        destination.write(chunk)
            else:
                # Download file from URL
                try:
                    response = requests.get(audio_url, stream=True, timeout=30)
                    response.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                except requests.RequestException as e:
                    return JsonResponse({
                        'error': f'Failed to download audio from URL: {str(e)}'
                    }, status=400)
            
            # Update task status
            external_task_status[task_id].update({
                "task_id": task_id,
                "filename": filename,
                "audio_file_path": file_path,
                "task_type": "external",
                "created_at": int(time.time()),
                "status": "Queued",
            })
            
            # Add to unified queue (same priority as internal tasks)
            subtitle_task_queue.put(task_id)
            
            return JsonResponse({
                'task_id': task_id,
                'status': 'queued',
                'message': 'Audio file queued for transcription',
                'queue_position': subtitle_task_queue.qsize()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ExternalTranscriptionStatusView(View):
    """
    Query transcription task status and results
    """
    http_method_names = ["get"]
    
    def get(self, request, task_id):
        if task_id not in external_task_status:
            return JsonResponse({'error': 'Task not found'}, status=404)
        
        task = external_task_status[task_id]
        response_data = {
            'task_id': task_id,
            'filename': task['filename'],
            'status': task['status'].lower(),
            'created_at': task['created_at'],
        }
        
        if task['status'] == 'Completed':
            response_data.update({
                'result_url': f'/video/external_transcription/{task_id}/result',
                'result_ready': True
            })
        elif task['status'] == 'Failed':
            response_data['error_message'] = task['error_message']
        
        # Add queue information
        if task['status'] == 'Queued':
            response_data['queue_size'] = subtitle_task_queue.qsize()
        
        return JsonResponse(response_data)


class ExternalTranscriptionResultView(View):
    """
    Download transcription result (SRT format)
    """
    http_method_names = ["get"]
    
    def get(self, request, task_id):
        if task_id not in external_task_status:
            return JsonResponse({'error': 'Task not found'}, status=404)
        
        task = external_task_status[task_id]
        if task['status'] != 'Completed':
            return JsonResponse({'error': 'Task not completed yet'}, status=400)
        
        result_file = task.get('result_file')
        if not result_file or not os.path.exists(result_file):
            return JsonResponse({'error': 'Result file not found'}, status=404)
        
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            response = HttpResponse(srt_content, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{task_id}.srt"'
            return response
            
        except Exception as e:
            return JsonResponse({'error': f'Error reading result file: {str(e)}'}, status=500)


class ExternalTranscriptionListView(View):
    """
    List all external transcription tasks with their status
    """
    http_method_names = ["get"]
    
    def get(self, request):
        tasks = []
        for task_id, task_data in external_task_status.items():
            tasks.append({
                'task_id': task_id,
                'filename': task_data['filename'],
                'status': task_data['status'].lower(),
                'created_at': task_data['created_at'],
                'task_type': task_data['task_type'],
            })
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda x: x['created_at'], reverse=True)
        
        return JsonResponse({
            'tasks': tasks,
            'queue_size': subtitle_task_queue.qsize()
        })


@method_decorator(csrf_exempt, name='dispatch')
class ExternalTranscriptionDeleteView(View):
    """
    Delete a transcription task and its associated files
    """
    http_method_names = ["delete", "post"]  # Support both DELETE and POST methods
    
    def delete(self, request, task_id):
        return self._handle_delete(task_id)
    
    def post(self, request, task_id):
        return self._handle_delete(task_id)
    
    def _handle_delete(self, task_id):
        if task_id not in external_task_status:
            return JsonResponse({'error': 'Task not found'}, status=404)
        
        task = external_task_status[task_id]
        
        # Clean up files
        try:
            if task.get('audio_file_path') and os.path.exists(task['audio_file_path']):
                os.remove(task['audio_file_path'])
            
            if task.get('result_file') and os.path.exists(task['result_file']):
                os.remove(task['result_file'])
        except Exception as e:
            print(f"Error cleaning up files for task {task_id}: {e}")
        
        # Remove from status tracking
        del external_task_status[task_id]
        
        return JsonResponse({'message': 'Task deleted successfully'})
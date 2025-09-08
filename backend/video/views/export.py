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
    """添加视频导出任务"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            video_id = data.get('video_id')
            subtitle_type = data.get('subtitle_type', 'raw')  # raw, translated, both
            
            if not video_id:
                return JsonResponse({
                    'success': False,
                    'message': '缺少视频ID'
                })
            
            # 检查视频是否存在
            try:
                video = Video.objects.get(pk=video_id)
            except Video.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': '视频不存在'
                })
            
            # 检查字幕文件是否存在
            if subtitle_type in ['raw', 'both'] and not video.srt_path:
                return JsonResponse({
                    'success': False,
                    'message': '该视频没有原文字幕文件'
                })
            
            if subtitle_type in ['translated', 'both'] and not video.translated_srt_path:
                return JsonResponse({
                    'success': False,
                    'message': '该视频没有译文字幕文件'
                })
            
            # 生成任务ID
            task_id = f"export_{video_id}_{int(time.time())}"
            
            # 初始化任务状态
            export_task_status[task_id].update({
                "video_id": video_id,
                "video_name": video.name,
                "subtitle_type": subtitle_type,
                "status": "Queued",
                "progress": 0,
                "output_filename": "",
                "error_message": "",
            })
            
            # 添加到队列
            export_queue.put(task_id)
            
            return JsonResponse({
                'success': True,
                'message': '导出任务已添加到队列',
                'task_id': task_id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '无效的JSON数据'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            })

class AllExportStatusView(View):
    """获取所有导出任务状态"""
    
    def get(self, request):
        return JsonResponse({
            'success': True,
            'data': dict(export_task_status)
        })

class ExportStatusView(View):
    """获取单个导出任务状态"""
    
    def get(self, request, task_id):
        if task_id not in export_task_status:
            return JsonResponse({
                'success': False,
                'message': '任务不存在'
            })
        
        return JsonResponse({
            'success': True,
            'data': export_task_status[task_id]
        })

@method_decorator(csrf_exempt, name='dispatch')
class DeleteExportTaskView(View):
    """删除导出任务"""
    
    def delete(self, request, task_id):
        if task_id not in export_task_status:
            return JsonResponse({
                'success': False,
                'message': '任务不存在'
            })
        
        task = export_task_status[task_id]
        
        # 删除输出文件（如果存在）
        import os
        if task['output_filename']:
            output_path = os.path.join('work_dir/export_videos', task['output_filename'])
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception as e:
                print(f"Failed to delete export file: {e}")
        
        # 从任务状态中删除
        del export_task_status[task_id]
        
        return JsonResponse({
            'success': True,
            'message': '任务已删除'
        })

@method_decorator(csrf_exempt, name='dispatch')
class RetryExportTaskView(View):
    """重试导出任务"""
    
    def post(self, request, task_id):
        if task_id not in export_task_status:
            return JsonResponse({
                'success': False,
                'message': '任务不存在'
            })
        
        task = export_task_status[task_id]
        
        # 重置任务状态
        export_update_status(task_id, "Queued", 0, "")
        task['output_filename'] = ""
        
        # 重新添加到队列
        export_queue.put(task_id)
        
        return JsonResponse({
            'success': True,
            'message': '任务已重新添加到队列'
        })

class ExportedVideoDownloadView(View):
    """下载导出的视频文件"""
    
    def get(self, request, task_id):
        if task_id not in export_task_status:
            raise Http404("任务不存在")
        
        task = export_task_status[task_id]
        
        # 检查任务状态和输出文件
        if task['status'] != 'Completed' or not task['output_filename']:
            raise Http404("文件不可用")
        
        # 构建文件路径
        export_dir = 'work_dir/export_videos'
        file_path = os.path.join(export_dir, task['output_filename'])
        
        if not os.path.exists(file_path):
            raise Http404("文件不存在")
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'video/mp4'
        
        # 处理 Range 请求（用于支持断点续传和视频播放器的快进）
        range_header = request.headers.get('Range')
        if range_header:
            import re
            # 解析 Range 请求头
            range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                
                if end >= file_size:
                    end = file_size - 1
                
                length = end - start + 1
                
                # 创建分片响应
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
        
        # 普通的完整文件下载
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
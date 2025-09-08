from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from ..models import Video
import json
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class MindmapActionView(View):
    """思维导图操作视图 - 统一处理增删改查"""
    
    def get(self, request, action, video_id):
        """处理GET请求"""
        if action == 'get':
            return self.get_mindmap(request, video_id)
        elif action == 'list':
            return self.list_videos_with_mindmap(request)
        else:
            return JsonResponse({
                'success': False,
                'error': f'不支持的操作: {action}'
            }, status=400)
    
    def post(self, request, action, video_id):
        """处理POST请求"""
        if action == 'update':
            return self.update_mindmap(request, video_id)
        else:
            return JsonResponse({
                'success': False,
                'error': f'不支持的操作: {action}'
            }, status=400)
    
    def delete(self, request, action, video_id):
        """处理DELETE请求"""
        if action == 'delete':
            return self.delete_mindmap(request, video_id)
        else:
            return JsonResponse({
                'success': False,
                'error': f'不支持的操作: {action}'
            }, status=400)
    
    def get_mindmap(self, request, video_id):
        """获取视频的思维导图内容"""
        try:
            video = get_object_or_404(Video, id=video_id)
            
            # 如果mindmap_content为空或None，返回空的节点数组
            mindmap_data = video.mindmap_content or {'nodes': []}
            
            return JsonResponse({
                'success': True,
                'mindmap_content': mindmap_data
            })
            
        except Exception as e:
            logger.error(f"Error getting mindmap for video {video_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def update_mindmap(self, request, video_id):
        """更新视频的思维导图内容"""
        try:
            video = get_object_or_404(Video, id=video_id)
            
            data = json.loads(request.body)
            mindmap_content = data.get('mindmap_content', {})
            
            # 验证数据结构 - 应该是包含nodes数组的JSON对象
            if not isinstance(mindmap_content, dict):
                return JsonResponse({
                    'success': False,
                    'error': '思维导图数据格式错误，应为JSON对象'
                }, status=400)
            
            # 验证内容大小（转为字符串检查）
            content_str = json.dumps(mindmap_content, ensure_ascii=False)
            if len(content_str) > 50000:  # 增加限制到50KB
                return JsonResponse({
                    'success': False,
                    'error': '思维导图内容过大，请简化内容'
                }, status=400)
            
            video.mindmap_content = mindmap_content
            video.save(update_fields=['mindmap_content'])
            
            return JsonResponse({
                'success': True,
                'message': '思维导图已保存'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '无效的JSON数据'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating mindmap for video {video_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def delete_mindmap(self, request, video_id):
        """删除视频的思维导图内容"""
        try:
            video = get_object_or_404(Video, id=video_id)
            
            video.mindmap_content = {'nodes': []}  # 重置为空的节点数组
            video.save(update_fields=['mindmap_content'])
            
            return JsonResponse({
                'success': True,
                'message': '思维导图已删除'
            })
            
        except Exception as e:
            logger.error(f"Error deleting mindmap for video {video_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def list_videos_with_mindmap(self, request):
        """列出所有有思维导图的视频"""
        try:
            videos = Video.objects.filter(mindmap_content__isnull=False).exclude(mindmap_content='')
            
            video_list = []
            for video in videos:
                video_list.append({
                    'id': video.id,
                    'name': video.name,
                    'has_mindmap': bool(video.mindmap_content),
                    'mindmap_preview': video.mindmap_content[:100] + '...' if len(video.mindmap_content or '') > 100 else video.mindmap_content
                })
            
            return JsonResponse({
                'success': True,
                'videos': video_list,
                'count': len(video_list)
            })
            
        except Exception as e:
            logger.error(f"Error listing videos with mindmap: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
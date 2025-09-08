# views/categories.py
from django.utils import timezone
from django.http import JsonResponse,HttpResponse,HttpResponseNotAllowed,HttpResponseNotFound,Http404,FileResponse
from django.core.exceptions import ObjectDoesNotExist
from .base import JsonView
from django.views import View
from ..models import Category, Video          # parent dir -> app root
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

@method_decorator(csrf_exempt, name="dispatch")
class CategoryActionView(View):
    """
    POST   /categories/            → add
    rename /categories/<old>/      → rename
    DELETE /categories/<name>/     → delete
    """
    def dispatch(self, request, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        print(self.action)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, video_id):
        if self.action == 'rename':
            return self.rename(request, video_id)
        elif self.action == 'delete':
            return self.delete(request, video_id)
        elif self.action == 'add':
            return self.add(request, video_id)
        # 其它动作不允许 POST
        return HttpResponseNotAllowed(['POST'])
    def get(self, request, video_id):
        if self.action == 'query':
            return self.query(request, video_id)
        elif self.action == 'edit':
            return self.edit(request, video_id)
    def query(self, request, *_, **__):
        try:
            categories = Category.objects.all().values('id', 'name')
            return JsonResponse({
                'success': True,
                'categories': list(categories)
            })
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'Could not retrieve categories: {str(e)}'},
                status=500
            )
    def query_videos(self, request, *_, **__):
        try:
            Video = self.get_object_or_404(Video, id=video_id,Category=Category)
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'Could not retrieve Videos from current category: {str(e)}'},
                status=500
            )
    def add(self, request, *_, **__):
        try:
            data = json.loads(request.body)
            category_name = data.get('categoryName')

            if not category_name:
                return JsonResponse(
                    {'success': False, 'error': 'Category name is required'},
                    status=400
                )

            # 检查分类是否已存在（不区分大小写）
            if Category.objects.filter(name__iexact=category_name).exists():
                return JsonResponse(
                    {'success': False, 'error': 'Category already exists'},
                    status=409
                )

            # 创建新分类
            new_category = Category.objects.create(
                name=category_name,
                created_time=timezone.now()
            )

            return JsonResponse({
                'success': True,
                'message': 'Category added successfully',
                'category': {
                    'id': new_category.id,
                    'name': new_category.name
                }
            })

        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'error': 'Invalid JSON format'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'Could not add category: {str(e)}'},
                status=500
            )

    def rename(self, request, id, **__):
        try:
            # 解析 JSON 数据
            data = json.loads(request.body)
            old_name = data.get('oldName')
            new_name = data.get('newName')
            print(old_name, new_name)
            # 参数验证
            if not old_name or not new_name:
                return JsonResponse(
                    {'error': 'Old or new category name missing'},
                    status=400
                )
            
            # 确保分类名称是字符串
            if not isinstance(old_name, str) or not isinstance(new_name, str):
                return JsonResponse(
                    {'error': 'Category names must be strings'},
                    status=400
                )
            # 更新分类名称
            # 如果新旧名称相同,则直接返回" name not changed "
            if old_name.lower() == new_name.lower():
                return JsonResponse({
                    'success': False,
                    'message': 'Category name unchanged'
                })
                
            # 检查新分类名称是否已存在
            if Category.objects.filter(name__iexact=new_name).exists():
                return JsonResponse(
                    {'error': 'New category name already exists'},
                    status=409
                )
            # 检查旧分类名称是否存在
            if not Category.objects.filter(name__iexact=old_name).exists():
                return JsonResponse(
                    {'error': 'Old category name does not exist'},
                    status=404
                )
            Category.objects.filter(name__iexact=old_name).update(name=new_name)
            updated = Video.objects.filter(category__name__iexact=new_name)
            # if updated == 0:
            #     return JsonResponse(
            #         {'error': 'No videos found with the specified category'},
            #         status=404
            #     )
            return JsonResponse({
                'success': True,
                'message': f'Renamed {updated} videos successfully'
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse(
                {'error': f'Could not rename category: {str(e)}'},
                status=500
            )

    def delete(self, request, name, **__):
        try:
            data = json.loads(request.body)
            category_name = data.get('categoryName')
            print(category_name)
            if not category_name:
                return JsonResponse(
                    {'success': False, 'error': 'Category name is required'},
                    status=400
                )

            # 获取分类对象
            category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                return JsonResponse(
                    {'success': False, 'error': 'Category not found'},
                    status=404
                )

            # 将该分类下的所有视频的category设为null
            Video.objects.filter(category=category).update(category=None)

            # 删除分类
            category.delete()

            return JsonResponse({
                'success': True,
                'message': 'Category deleted successfully'
            })

        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'error': 'Invalid JSON format'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'Could not delete category: {str(e)}'},
                status=500
            )
        
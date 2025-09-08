# views/collections.py
from django.http import JsonResponse,HttpResponse,HttpResponseNotAllowed,HttpResponseNotFound,Http404,FileResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings  # Ensure this is at the top
from django.shortcuts import get_object_or_404,render
from django.urls import reverse
from .base import JsonView
from django.views import View
from ..models import Collection, Category
from ..utils import calc_diff_time
from .videos import get_user_combined_hidden_categories
import os
import json
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name="dispatch")
class CollectionActionView(View):
    def dispatch(self, request, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        print(self.action)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, collection_id):
        if self.action == 'create':# 创建合集，collection_id是0.
            return self.upload(request, collection_id)
        elif self.action == 'delete':
            return self.delete(request, collection_id)
        elif self.action == 'rename':
            return self.rename(request, collection_id)
        elif self.action == 'move_category': # 移动Collection的分类
            return self.move_category(request, collection_id)
        elif self.action == 'update_thumbnail':
            return self.update_thumbnail(request, collection_id)
        elif self.action == 'update':
            return self.update_collection(request, collection_id)
        # 其它动作不允许 POST
        return HttpResponseNotAllowed(['POST'])

    def get(self, request, collection_id):
        if self.action == 'query':
            return self.query(request, collection_id)
        elif self.action == 'list':
            return self.list_all(request)
        elif self.action == 'videos':
            return self.get_collection_videos(request, collection_id)
        
    # ---------- 列出所有Collections，可以选择collection，或者反选，排除部分Category中的内容 ----------
    def list_all(self, request):
        """
        列出所有Collections，可按Category筛选
        """
        category_id = request.GET.get('category_id')
        
        # 获取用户的组合隐藏分类ID列表（系统设置 + 用户自定义）
        hidden_category_ids = get_user_combined_hidden_categories(request)
        
        # 构建查询条件
        if category_id:
            if category_id == '0':  # 0表示无分类
                collections = Collection.objects.filter(category__isnull=True)
            else:
                try:
                    collections = Collection.objects.filter(category_id=category_id)
                except ValueError:
                    return JsonResponse(
                        {"success": False, "message": "Invalid category_id"}, status=400
                    )
        else:
            collections = Collection.objects.all()
        
        # 过滤掉属于隐藏分类的合集
        if hidden_category_ids:
            collections = collections.exclude(category_id__in=hidden_category_ids)
        
        # 按最后修改时间倒序排列
        collections = collections.order_by('-last_modified')
        
        collection_list = []
        for collection in collections:
            video_count = collection.videos.count()
            collection_list.append({
                "id": collection.id,
                "name": collection.name,
                "category_id": collection.category.id if collection.category else 0,
                "category_name": collection.category.name if collection.category else "No Category",
                "thumbnail_url": collection.thumbnail_url,
                "created_time": collection.created_time.isoformat() if collection.created_time else None,
                "last_modified": collection.last_modified.isoformat() if collection.last_modified else None,
                "video_count": video_count
            })

        return JsonResponse({
            "success": True,
            "collections": collection_list,
            "total_count": len(collection_list)
        }, status=200)
    
    def rename(self,request,collection_id):
        data = json.loads(request.body)
        new_name = data.get('newName')

        if not new_name:
            return JsonResponse(
                {'success': False, 'message': 'Get no new name'},
                status=400
            )

        try:
            collection = Collection.objects.get(pk=collection_id)
        except ObjectDoesNotExist:
            return JsonResponse(
                {'success': False, 'message': 'collection not found'},
                status=404
            )

        collection.name = new_name
        collection.last_modified = timezone.now()
        collection.save(update_fields=['name', 'last_modified'])

        return JsonResponse(
            {'success': True, 'message': 'collection renamed successfully'},
            status=200
        )
    
    # ---------- 查询Collection详细信息 ----------
    def query(self, request, collection_id):
        """
        查询Collection详细信息，包括其关联的视频列表
        """
        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Collection not found"}, status=404
            )
        
        # 获取Collection下的所有视频
        videos = collection.videos.all()
        video_list = []
        for video in videos:
            video_list.append({
                "id": video.id,
                "name": video.name,
                "url": video.url,
                "thumbnail_url": video.thumbnail_url,
                "video_length": video.video_length,
                "last_modified": video.last_modified.isoformat() if video.last_modified else None,
            })

        return JsonResponse({
            "success": True,
            "collection": {
                "id": collection.id,
                "name": collection.name,
                "category_id": collection.category.id if collection.category else 0,
                "category_name": collection.category.name if collection.category else "No Category",
                "thumbnail_url": collection.thumbnail_url,
                "created_time": collection.created_time.isoformat(),
                "last_modified": collection.last_modified.isoformat(),
                "video_count": videos.count(),
                "videos": video_list
            }
        }, status=200)
    
    # @method_decorator(csrf_exempt)
    def update_thumbnail(self, request, collection_id):
        """
        POST /collections/update_thumbnail/<collection_id>
        接收前端上传的缩略图文件保存到 `MEDIA_ROOT/collection_thumbnail/`，
        并更新 Collection.thumbnail_url 字段。
        """
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        if "thumbnail_file" not in request.FILES:
            return JsonResponse({"error": "No thumbnail file part"}, status=400)

        file = request.FILES["thumbnail_file"]
        if not file.name:
            return JsonResponse({"error": "No selected file"}, status=400)

        # 1. 取得目标 Collection
        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            return JsonResponse({"error": "Collection not found"}, status=404)

        # 2. 生成保存路径
        # thumb_dir = os.path.join(settings.MEDIA_ROOT, "collection_thumbnail")
        thumb_dir = os.path.join(settings.MEDIA_ROOT, "thumbnail")
        os.makedirs(thumb_dir, exist_ok=True)

        ext = os.path.splitext(file.name)[1] or ".jpg"
        # 使用collection url作为缩略图文件名，防止重复
        filename = os.path.splitext(os.path.basename(collection.name))[0]  # 获取文件名，不包含扩展名
        thumb_filename = f"{filename}{ext}"
        thumb_path = os.path.join(thumb_dir, thumb_filename)

        # 3. 写入文件
        with open(thumb_path, "wb+") as dst:
            for chunk in file.chunks():
                dst.write(chunk)

        # 4. 更新模型
        collection.thumbnail_url = thumb_filename
        collection.last_modified = timezone.now()
        collection.save(update_fields=["thumbnail_url", "last_modified"])

        return JsonResponse(
            {"success": True, "thumbnail_url": thumb_filename}, status=200
        )

    # ---------- 删除合集 ----------
    def delete(self, request, collection_id):
        """
        只有当 Collection 不含任何 Video 时才允许物理删除。
        """
        try:
            target = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Collection not found"}, status=404
            )

        # 0️⃣ 先检查是否有视频
        if target.videos.exists():
            return JsonResponse(
                {
                    "success": False,
                    "message": "该合集仍包含视频，清空后才能删除",
                },
                status=400,
            )

        target.delete()
        return JsonResponse(
            {"success": True, "message": "Collection deleted successfully"}, status=200
        )

    # ---------- 创建合集 ----------
    def upload(self, request, collection_id):
        """
        创建新的Collection。需要name参数，可选category_id (默认0表示无分类)。
        ID在数据库中自动从1开始递增。
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Invalid JSON data"}, status=400
            )

        collection_name = data.get('name', '').strip()
        category_id = data.get('category_id', 0)  # 默认0表示无分类

        if not collection_name:
            return JsonResponse(
                {"success": False, "message": "Collection name is required"}, status=400
            )

        # 检查Collection名称是否已存在
        if Collection.objects.filter(name=collection_name).exists():
            return JsonResponse(
                {"success": False, "message": "Collection with this name already exists"}, status=400
            )

        # 处理分类绑定
        category = None
        if category_id != 0:  # 0表示无分类
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                return JsonResponse(
                    {"success": False, "message": "Category not found"}, status=404
                )

        # 创建Collection (ID会自动从1开始递增)
        try:
            collection = Collection.objects.create(
                name=collection_name,
                category=category,  # None表示无分类
                last_modified=timezone.now()
            )
            
            return JsonResponse({
                "success": True,
                "message": "Collection created successfully",
                "collection": {
                    "id": collection.id,
                    "name": collection.name,
                    "category_id": collection.category.id if collection.category else 0,
                    "category_name": collection.category.name if collection.category else "No Category",
                    "created_time": collection.created_time.isoformat(),
                    "last_modified": collection.last_modified.isoformat()
                }
            }, status=201)
            
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Failed to create collection: {str(e)}"}, status=500
            )

    # ---------- 移动Collection到其他Category ----------
    def move_category(self, request, collection_id):
        """
        移动Collection到其他Category
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Invalid JSON data"}, status=400
            )

        new_category_id = data.get('category_id', 0)

        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Collection not found"}, status=404
            )

        # 处理新分类
        new_category = None
        if new_category_id != 0:  # 0表示无分类
            try:
                new_category = Category.objects.get(pk=new_category_id)
            except Category.DoesNotExist:
                return JsonResponse(
                    {"success": False, "message": "Target category not found"}, status=404
                )

        collection.category = new_category
        collection.last_modified = timezone.now()
        collection.save(update_fields=["category", "last_modified"])

        # Also update all videos in this collection to the same category
        videos_in_collection = collection.videos.all()
        videos_updated = 0
        if videos_in_collection.exists():
            videos_updated = videos_in_collection.update(
                category=new_category,
                last_modified=timezone.now()
            )

        return JsonResponse({
            "success": True,
            "message": f"Collection and {videos_updated} videos moved successfully",
            "collection": {
                "id": collection.id,
                "name": collection.name,
                "category_id": collection.category.id if collection.category else 0,
                "category_name": collection.category.name if collection.category else "No Category",
            },
            "videos_updated": videos_updated
        }, status=200)

    # ---------- 通用更新Collection信息 ----------
    def update_collection(self, request, collection_id):
        """
        通用更新Collection信息 (name, category等)
        """
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Invalid JSON data"}, status=400
            )

        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Collection not found"}, status=404
            )

        # 更新字段
        updated_fields = ["last_modified"]
        
        # 更新名称
        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                return JsonResponse(
                    {"success": False, "message": "Collection name cannot be empty"}, status=400
                )
            # 检查名称是否已存在（排除当前Collection）
            if Collection.objects.filter(name=new_name).exclude(pk=collection_id).exists():
                return JsonResponse(
                    {"success": False, "message": "Collection with this name already exists"}, status=400
                )
            collection.name = new_name
            updated_fields.append("name")

        # 更新分类
        if 'category_id' in data:
            category_id = data['category_id']
            if category_id == 0:  # 0表示无分类
                collection.category = None
            else:
                try:
                    category = Category.objects.get(pk=category_id)
                    collection.category = category
                except Category.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "message": "Category not found"}, status=404
                    )
            updated_fields.append("category")

        # 更新最后修改时间
        collection.last_modified = timezone.now()
        collection.save(update_fields=updated_fields)

        return JsonResponse({
            "success": True,
            "message": "Collection updated successfully",
            "collection": {
                "id": collection.id,
                "name": collection.name,
                "category_id": collection.category.id if collection.category else 0,
                "category_name": collection.category.name if collection.category else "No Category",
                "last_modified": collection.last_modified.isoformat()
            }
        }, status=200)
    
    def get_collection_videos(self, request, collection_id):
        """
        获取合集中的所有视频
        GET /collection/videos/<collection_id>
        """
        try:
            collection = get_object_or_404(Collection, pk=collection_id)
            
            # 获取合集中的所有视频，按last_modified倒序排列
            videos = collection.videos.all().order_by('-last_modified')
            
            video_list = []
            for video in videos:
                video_list.append({
                    "id": video.id,
                    "name": video.name,
                    "url": video.url,
                    "thumbnail": f"img/{video.thumbnail_url}" if video.thumbnail_url else "",
                    "length": video.video_length or "00:00",
                    "last_modified": calc_diff_time(video.last_modified or timezone.now()),
                    "type": "video"
                })
            
            return JsonResponse({
                'success': True,
                'videos': video_list,
                'collection': {
                    'id': collection.id,
                    'name': collection.name,
                    'video_count': len(video_list)
                }
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
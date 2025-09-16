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
        if self.action == 'create':# Create collection, collection_id is 0.
            return self.upload(request, collection_id)
        elif self.action == 'delete':
            return self.delete(request, collection_id)
        elif self.action == 'rename':
            return self.rename(request, collection_id)
        elif self.action == 'move_category': # Move Collection's category
            return self.move_category(request, collection_id)
        elif self.action == 'update_thumbnail':
            return self.update_thumbnail(request, collection_id)
        elif self.action == 'update':
            return self.update_collection(request, collection_id)
        # Other actions not allowed for POST
        return HttpResponseNotAllowed(['POST'])

    def get(self, request, collection_id):
        if self.action == 'query':
            return self.query(request, collection_id)
        elif self.action == 'list':
            return self.list_all(request)
        elif self.action == 'videos':
            return self.get_collection_videos(request, collection_id)
        
    # ---------- List all Collections, can select collection or exclude content from certain Categories ----------
    def list_all(self, request):
        """
        List all Collections, can filter by Category
        """
        category_id = request.GET.get('category_id')
        
        # Get user's combined hidden category ID list (system settings + user customization)
        hidden_category_ids = get_user_combined_hidden_categories(request)
        
        # Build query conditions
        if category_id:
            if category_id == '0':  # 0 means no category
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
        
        # Filter out collections belonging to hidden categories
        if hidden_category_ids:
            collections = collections.exclude(category_id__in=hidden_category_ids)
        
        # Sort by last modified time in descending order
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
    
    # ---------- Query Collection details ----------
    def query(self, request, collection_id):
        """
        Query Collection details, including its associated video list
        """
        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Collection not found"}, status=404
            )
        
        # Get all videos under the Collection
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

        # 1. Get target Collection
        try:
            collection = Collection.objects.get(pk=collection_id)
        except Collection.DoesNotExist:
            return JsonResponse({"error": "Collection not found"}, status=404)

        # 2. Generate save path
        # thumb_dir = os.path.join(settings.MEDIA_ROOT, "collection_thumbnail")
        thumb_dir = os.path.join(settings.MEDIA_ROOT, "thumbnail")
        os.makedirs(thumb_dir, exist_ok=True)

        ext = os.path.splitext(file.name)[1] or ".jpg"
        # Use collection url as thumbnail filename to prevent duplicates
        filename = os.path.splitext(os.path.basename(collection.name))[0]  # Get filename without extension
        thumb_filename = f"{filename}{ext}"
        thumb_path = os.path.join(thumb_dir, thumb_filename)

        # 3. Write file
        with open(thumb_path, "wb+") as dst:
            for chunk in file.chunks():
                dst.write(chunk)

        # 4. Update model
        collection.thumbnail_url = thumb_filename
        collection.last_modified = timezone.now()
        collection.save(update_fields=["thumbnail_url", "last_modified"])

        return JsonResponse(
            {"success": True, "thumbnail_url": thumb_filename}, status=200
        )

    # ---------- Delete collection ----------
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

        # 0️⃣ First check if there are any videos
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

    # ---------- Create collection ----------
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
        category_id = data.get('category_id', 0)  # Default 0 means no category

        if not collection_name:
            return JsonResponse(
                {"success": False, "message": "Collection name is required"}, status=400
            )

        # Check if Collection name already exists
        if Collection.objects.filter(name=collection_name).exists():
            return JsonResponse(
                {"success": False, "message": "Collection with this name already exists"}, status=400
            )

        # Handle category binding
        category = None
        if category_id != 0:  # 0 means no category
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                return JsonResponse(
                    {"success": False, "message": "Category not found"}, status=404
                )

        # Create Collection (ID will automatically increment from 1)
        try:
            collection = Collection.objects.create(
                name=collection_name,
                category=category,  # None means no category
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

    # ---------- Move Collection to other Category ----------
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

        # Handle new category
        new_category = None
        if new_category_id != 0:  # 0 means no category
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

    # ---------- Generic update Collection information ----------
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

        # Update fields
        updated_fields = ["last_modified"]
        
        # Update name
        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                return JsonResponse(
                    {"success": False, "message": "Collection name cannot be empty"}, status=400
                )
            # Check if name already exists (excluding current Collection)
            if Collection.objects.filter(name=new_name).exclude(pk=collection_id).exists():
                return JsonResponse(
                    {"success": False, "message": "Collection with this name already exists"}, status=400
                )
            collection.name = new_name
            updated_fields.append("name")

        # Update category
        if 'category_id' in data:
            category_id = data['category_id']
            if category_id == 0:  # 0 means no category
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

        # Update last modified time
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
            
            # Get all videos in the collection, sorted by last_modified in descending order
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
    
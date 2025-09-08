from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.views.static import serve
import os

def index(request):
    """
    服务前端 Vue 应用的主入口
    """
    # 读取构建后的 index.html 文件
    static_dir = settings.STATIC_ROOT if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT and os.path.exists(settings.STATIC_ROOT) else settings.STATICFILES_DIRS[0]
    index_path = os.path.join(static_dir, 'index.html')
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HttpResponse(html_content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse(
            '<h1>Frontend not found</h1><p>Please run: npm run build and copy files to static/</p>', 
            status=404
        )

def frontend_assets(request, path):
    """
    服务前端静态资源 (CSS, JS, 图片等)
    """
    static_dir = settings.STATIC_ROOT if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT and os.path.exists(settings.STATIC_ROOT) else settings.STATICFILES_DIRS[0]
    file_path = os.path.join(static_dir, 'assets', path)
    
    if os.path.exists(file_path):
        return serve(request, path, document_root=os.path.join(static_dir, 'assets'))
    else:
        return HttpResponse('Asset not found', status=404)
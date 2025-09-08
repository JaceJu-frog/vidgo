from django.http import JsonResponse, Http404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
import json
from utils.audio.waveform_generator import get_waveform_for_file


@method_decorator(csrf_exempt, name='dispatch')
class WaveformAPIView(View):
    """
    为音频文件提供波形峰值数据的API端点
    
    GET /api/waveform/<filename> - 获取指定音频文件的波形数据
    """
    
    def get(self, request, filename):
        """
        获取音频文件的波形峰值数据
        
        Args:
            filename: 音频文件名前缀或完整文件名（不含路径）
            
        Returns:
            JsonResponse: 包含波形数据的JSON响应
        """
        try:
            # 解码URL编码的文件名
            import urllib.parse
            decoded_filename = urllib.parse.unquote(filename)
            
            # 如果输入的是前缀，查找匹配的音频文件
            actual_filename = self._find_audio_file_by_prefix(decoded_filename)
            if actual_filename is None:
                return JsonResponse({
                    'error': 'No matching audio file found',
                    'prefix': decoded_filename
                }, status=404)
            
            # 获取波形数据
            waveform_data = get_waveform_for_file(actual_filename)
            
            if waveform_data is None:
                return JsonResponse({
                    'error': 'Failed to generate or retrieve waveform data',
                    'filename': actual_filename
                }, status=404)
            
            # 添加额外的元数据
            response_data = {
                **waveform_data,
                'generated_at': 'server-side',
                'api_version': '1.0',
                'matched_filename': actual_filename
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'filename': filename
            }, status=500)
    
    def _find_audio_file_by_prefix(self, prefix):
        """
        根据前缀查找音频文件
        
        Args:
            prefix: 文件名前缀
            
        Returns:
            str: 匹配的完整文件名，如果没找到返回None
        """
        # 如果已经是完整文件名且存在，直接返回
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, "..", "..")
        
        # 音频格式列表
        audio_formats = ['.mp3', '.m4a', '.aac', '.wav', '.flac', '.alac']
        
        # 如果输入已经包含扩展名，先尝试直接匹配
        if '.' in prefix:
            for dir_name in ["saved_audio", "saved_video"]:
                test_path = os.path.join(project_root, "media", dir_name, prefix)
                test_path = os.path.normpath(test_path)
                if os.path.exists(test_path):
                    return prefix
        
        # 在saved_audio和saved_video目录中查找以prefix开头的文件
        for dir_name in ["saved_audio", "saved_video"]:
            dir_path = os.path.join(project_root, "media", dir_name)
            dir_path = os.path.normpath(dir_path)
            
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    # 检查是否以前缀开头且是音频格式
                    if filename.startswith(prefix):
                        file_ext = os.path.splitext(filename)[1].lower()
                        if file_ext in audio_formats:
                            return filename
        
        return None


@method_decorator(csrf_exempt, name='dispatch') 
class WaveformListView(View):
    """
    列出所有可用的波形数据文件
    
    GET /api/waveform/list - 列出所有已生成的波形数据
    """
    
    def get(self, request):
        """
        列出所有已生成的波形数据文件
        
        Returns:
            JsonResponse: 包含波形文件列表的JSON响应
        """
        try:
            # 获取波形数据目录
            from django.conf import settings
            import os
            
            # 构建波形数据目录路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, "..", "..")
            waveform_dir = os.path.join(project_root, "media", "waveform_data")
            waveform_dir = os.path.normpath(waveform_dir)
            
            waveform_files = []
            
            if os.path.exists(waveform_dir):
                for filename in os.listdir(waveform_dir):
                    if filename.endswith('.peaks.json'):
                        file_path = os.path.join(waveform_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                            # 提取基本信息
                            base_name = filename.replace('.peaks.json', '')
                            file_info = {
                                'filename': filename,
                                'audio_file': data.get('audio_file', ''),
                                'duration': data.get('duration', 0),
                                'peaks_count': data.get('length', 0),
                                'file_size': os.path.getsize(file_path),
                                'last_modified': os.path.getmtime(file_path)
                            }
                            waveform_files.append(file_info)
                            
                        except Exception as e:
                            # 跳过损坏的文件
                            continue
            
            return JsonResponse({
                'waveform_files': waveform_files,
                'total_count': len(waveform_files),
                'directory': waveform_dir
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
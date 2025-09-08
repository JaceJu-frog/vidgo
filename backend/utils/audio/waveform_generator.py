import json
import subprocess
import numpy as np
import os
from typing import List, Tuple, Optional


def generate_waveform_peaks(
    audio_path: str,
    output_path: Optional[str] = None,
    samples_per_second: int = 20,
    bit_depth: int = 16
) -> List[float]:
    """
    为音频文件生成波形峰值数据用于前端可视化展示
    
    Args:
        audio_path: 音频文件路径
        output_path: 可选的JSON输出文件路径，如果不提供则自动生成
        samples_per_second: 每秒采样数（控制波形精度）
        bit_depth: 音频位深度
        
    Returns:
        List[float]: 峰值数据数组，每个值范围在[-1.0, 1.0]
        
    Raises:
        FileNotFoundError: 音频文件不存在
        subprocess.CalledProcessError: FFmpeg处理失败
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # 生成输出路径
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_dir = os.path.join(os.path.dirname(audio_path), "..", "waveform_data")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{base_name}.peaks.json")
    
    # 获取音频信息
    duration = _get_audio_duration(audio_path)
    if duration <= 0:
        raise ValueError(f"Invalid audio duration: {duration}")
    
    # 使用FFmpeg提取音频数据
    raw_audio_data = _extract_audio_data(audio_path, samples_per_second)
    
    # 计算峰值数据
    peaks = _calculate_peaks(raw_audio_data, samples_per_second, duration)
    
    # 保存峰值数据到JSON文件
    peak_data = {
        "version": "1.0",
        "audio_file": os.path.basename(audio_path),
        "duration": duration,
        "samples_per_second": samples_per_second,
        "length": len(peaks),
        "peaks": peaks
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(peak_data, f, indent=2)
    
    print(f"Waveform peaks generated: {output_path}")
    return peaks


def _get_audio_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    cmd = [
        'ffprobe', 
        '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'csv=p=0',
        audio_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        raise ValueError(f"Failed to get audio duration: {e}")


def _extract_audio_data(audio_path: str, sample_rate: int) -> np.ndarray:
    """使用FFmpeg提取音频原始数据"""
    cmd = [
        'ffmpeg',
        '-i', audio_path,
        '-f', 'f32le',  # 32位浮点格式
        '-ac', '1',     # 单声道
        '-ar', str(sample_rate * 100),  # 足够的采样率用于后续下采样
        '-'
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        # 将字节数据转换为float32数组
        audio_data = np.frombuffer(result.stdout, dtype=np.float32)
        return audio_data
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed to extract audio data: {e}")


def _calculate_peaks(audio_data: np.ndarray, samples_per_second: int, duration: float) -> List[float]:
    """从原始音频数据计算峰值"""
    if len(audio_data) == 0:
        return []
    
    # 计算每个峰值点对应的音频样本数
    total_samples = len(audio_data)
    target_peaks = int(duration * samples_per_second)
    samples_per_peak = total_samples // target_peaks if target_peaks > 0 else total_samples
    
    peaks = []
    
    # 分段计算峰值
    for i in range(0, total_samples, samples_per_peak):
        segment = audio_data[i:i + samples_per_peak]
        if len(segment) > 0:
            # 使用RMS值作为峰值（比简单的max更平滑）
            rms = np.sqrt(np.mean(segment ** 2))
            # 限制在[-1.0, 1.0]范围内
            peak = np.clip(rms, -1.0, 1.0)
            peaks.append(float(peak))
    
    return peaks


def get_waveform_for_file(filename: str) -> Optional[dict]:
    """
    为给定的音频或视频文件名获取或生成波形数据
    
    Args:
        filename: 文件名（不含路径，包含扩展名），可以是音频或视频文件
        
    Returns:
        dict: 包含波形数据的字典，如果失败则返回None
    """
    # 构建完整路径 - 先尝试音频目录，再尝试视频目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, "..", "..")
    
    # 检查文件扩展名决定优先搜索目录
    file_extension = os.path.splitext(filename)[1].lower()
    audio_formats = ['.mp3', '.m4a', '.aac', '.wav', '.flac', '.alac']
    video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    file_path = None
    
    if file_extension in audio_formats:
        # 音频文件，先检查saved_audio目录
        audio_path = os.path.join(project_root, "media", "saved_audio", filename)
        audio_path = os.path.normpath(audio_path)
        if os.path.exists(audio_path):
            file_path = audio_path
        else:
            # 也检查saved_video目录（以防音频文件被放在那里）
            video_path = os.path.join(project_root, "media", "saved_video", filename)
            video_path = os.path.normpath(video_path)
            if os.path.exists(video_path):
                file_path = video_path
    elif file_extension in video_formats:
        # 视频文件，先检查saved_video目录
        video_path = os.path.join(project_root, "media", "saved_video", filename)
        video_path = os.path.normpath(video_path)
        if os.path.exists(video_path):
            file_path = video_path
        else:
            # 也检查saved_audio目录（以防视频文件被放在那里）
            audio_path = os.path.join(project_root, "media", "saved_audio", filename)
            audio_path = os.path.normpath(audio_path)
            if os.path.exists(audio_path):
                file_path = audio_path
    else:
        # 未知格式，尝试两个目录
        for dir_name in ["saved_audio", "saved_video"]:
            test_path = os.path.join(project_root, "media", dir_name, filename)
            test_path = os.path.normpath(test_path)
            if os.path.exists(test_path):
                file_path = test_path
                break
    
    if not file_path:
        print(f"Audio/Video file not found in saved_audio or saved_video: {filename}")
        return None
    
    # 检查是否已有峰值数据
    base_name = os.path.splitext(filename)[0]
    waveform_dir = os.path.join(project_root, "media", "waveform_data")
    os.makedirs(waveform_dir, exist_ok=True)
    peaks_path = os.path.join(waveform_dir, f"{base_name}.peaks.json")
    peaks_path = os.path.normpath(peaks_path)
    
    # 如果峰值文件不存在或比音频/视频文件旧，则重新生成
    if not os.path.exists(peaks_path) or os.path.getmtime(peaks_path) < os.path.getmtime(file_path):
        try:
            generate_waveform_peaks(file_path, peaks_path)
        except Exception as e:
            print(f"Failed to generate waveform peaks: {e}")
            return None
    
    # 读取峰值数据
    try:
        with open(peaks_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read waveform peaks: {e}")
        return None


if __name__ == "__main__":
    # 测试函数
    test_audio = "一部关于糖的电影---最甜蜜的慢性杀手就在我们身边(双语字幕).mp3"
    result = get_waveform_for_file(test_audio)
    if result:
        print(f"Generated waveform with {len(result['peaks'])} peaks")
        print(f"Duration: {result['duration']:.2f} seconds")
    else:
        print("Failed to generate waveform")
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
    Generate waveform peak data for audio files for frontend visualization

    Args:
        audio_path: Path to audio file
        output_path: Optional JSON output file path, auto-generated if not provided
        samples_per_second: Samples per second (controls waveform precision)
        bit_depth: Audio bit depth

    Returns:
        List[float]: Peak data array, each value in range [-1.0, 1.0]

    Raises:
        FileNotFoundError: Audio file does not exist
        subprocess.CalledProcessError: FFmpeg processing failed
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Generate output path
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_dir = os.path.join(os.path.dirname(audio_path), "..", "waveform_data")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{base_name}.peaks.json")
    
    # Get audio information
    duration = _get_audio_duration(audio_path)
    if duration <= 0:
        raise ValueError(f"Invalid audio duration: {duration}")
    
    # Extract audio data using FFmpeg
    raw_audio_data = _extract_audio_data(audio_path, samples_per_second)
    
    # Calculate peak data
    peaks = _calculate_peaks(raw_audio_data, samples_per_second, duration)
    
    # Save peak data to JSON file
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
    """Get audio duration in seconds"""
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
    """Extract raw audio data using FFmpeg"""
    cmd = [
        'ffmpeg',
        '-i', audio_path,
        '-f', 'f32le',  # 32-bit float format
        '-ac', '1',     # Mono channel
        '-ar', str(sample_rate * 100),  # High sample rate for subsequent downsampling
        '-'
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        # Convert byte data to float32 array
        audio_data = np.frombuffer(result.stdout, dtype=np.float32)
        return audio_data
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed to extract audio data: {e}")


def _calculate_peaks(audio_data: np.ndarray, samples_per_second: int, duration: float) -> List[float]:
    """Calculate peaks from raw audio data"""
    if len(audio_data) == 0:
        return []
    
    # Calculate audio samples per peak point
    total_samples = len(audio_data)
    target_peaks = int(duration * samples_per_second)
    samples_per_peak = total_samples // target_peaks if target_peaks > 0 else total_samples
    
    peaks = []
    
    # Calculate peaks by segments
    for i in range(0, total_samples, samples_per_peak):
        segment = audio_data[i:i + samples_per_peak]
        if len(segment) > 0:
            # Use RMS value as peak (smoother than simple max)
            rms = np.sqrt(np.mean(segment ** 2))
            # Clamp to [-1.0, 1.0] range
            peak = np.clip(rms, -1.0, 1.0)
            peaks.append(float(peak))
    
    return peaks


def get_waveform_for_file(filename: str) -> Optional[dict]:
    """
    Get or generate waveform data for a given audio or video filename

    Args:
        filename: Filename (without path, with extension), can be audio or video file

    Returns:
        dict: Dictionary containing waveform data, None if failed
    """
    # Build full path - try audio directory first, then video directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, "..", "..")
    
    # Check file extension to determine priority search directory
    file_extension = os.path.splitext(filename)[1].lower()
    audio_formats = ['.mp3', '.m4a', '.aac', '.wav', '.flac', '.alac']
    video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    file_path = None
    
    if file_extension in audio_formats:
        # Audio file, check saved_audio directory first
        audio_path = os.path.join(project_root, "media", "saved_audio", filename)
        audio_path = os.path.normpath(audio_path)
        if os.path.exists(audio_path):
            file_path = audio_path
        else:
            # Also check saved_video directory (in case audio file is stored there)
            video_path = os.path.join(project_root, "media", "saved_video", filename)
            video_path = os.path.normpath(video_path)
            if os.path.exists(video_path):
                file_path = video_path
    elif file_extension in video_formats:
        # Video file, check saved_video directory first
        video_path = os.path.join(project_root, "media", "saved_video", filename)
        video_path = os.path.normpath(video_path)
        if os.path.exists(video_path):
            file_path = video_path
        else:
            # Also check saved_audio directory (in case video file is stored there)
            audio_path = os.path.join(project_root, "media", "saved_audio", filename)
            audio_path = os.path.normpath(audio_path)
            if os.path.exists(audio_path):
                file_path = audio_path
    else:
        # Unknown format, try both directories
        for dir_name in ["saved_audio", "saved_video"]:
            test_path = os.path.join(project_root, "media", dir_name, filename)
            test_path = os.path.normpath(test_path)
            if os.path.exists(test_path):
                file_path = test_path
                break
    
    if not file_path:
        print(f"Audio/Video file not found in saved_audio or saved_video: {filename}")
        return None
    
    # Check if peak data already exists
    base_name = os.path.splitext(filename)[0]
    waveform_dir = os.path.join(project_root, "media", "waveform_data")
    os.makedirs(waveform_dir, exist_ok=True)
    peaks_path = os.path.join(waveform_dir, f"{base_name}.peaks.json")
    peaks_path = os.path.normpath(peaks_path)
    
    # If peak file doesn't exist or is older than audio/video file, regenerate
    if not os.path.exists(peaks_path) or os.path.getmtime(peaks_path) < os.path.getmtime(file_path):
        try:
            generate_waveform_peaks(file_path, peaks_path)
        except Exception as e:
            print(f"Failed to generate waveform peaks: {e}")
            return None
    
    # Read peak data
    try:
        with open(peaks_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read waveform peaks: {e}")
        return None


if __name__ == "__main__":
    # Test function
    test_audio = "一部关于糖的电影---最甜蜜的慢性杀手就在我们身边(双语字幕).mp3"
    result = get_waveform_for_file(test_audio)
    if result:
        print(f"Generated waveform with {len(result['peaks'])} peaks")
        print(f"Duration: {result['duration']:.2f} seconds")
    else:
        print("Failed to generate waveform")
"""
Video conversion utilities for transcoding videos to AV1 format
"""
import os
import subprocess
import logging
import multiprocessing
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class VideoConverter:
    """Handles video conversion to AV1 format using FFmpeg"""
    
    def __init__(self):
        self.ffmpeg_path = "ffmpeg"  # Assumes ffmpeg is in PATH
        self._detect_hardware_support()
        
    def check_codec(self, video_path: str) -> Optional[str]:
        """
        Check the video codec of a file using ffprobe
        Returns: codec name (e.g., 'hevc', 'h264', 'av1') or None if detection fails
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                codec = result.stdout.strip()
                logger.info(f"Detected codec for {video_path}: {codec}")
                return codec
            else:
                logger.error(f"ffprobe failed for {video_path}: {result.stderr}")
                return None
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Error detecting codec for {video_path}: {e}")
            return None
    
    def should_convert_to_av1(self, video_path: str) -> bool:
        """
        Determine if a video should be converted to AV1
        Returns True if video is HEVC/H.265 or other non-AV1 codecs that have poor browser support
        """
        codec = self.check_codec(video_path)
        if not codec:
            return False
            
        # Convert HEVC, H.265, and other problematic codecs to AV1
        problematic_codecs = ['hevc', 'h265', 'mpeg4', 'mpeg2video']
        return codec.lower() in problematic_codecs
    
    def _detect_hardware_support(self):
        """Detect available hardware encoders for AV1"""
        self.hw_encoders = {
            'nvidia': False,
            'amd': False,
            'intel': False
        }
        
        try:
            # Check for encoder availability first
            result = subprocess.run([self.ffmpeg_path, '-encoders'], 
                                  capture_output=True, text=True, timeout=10)
            encoders = result.stdout
            
            # Test each encoder by actually trying to use it
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                test_input = os.path.join(temp_dir, "test_input.mp4")
                
                # Create tiny test video
                subprocess.run([
                    'ffmpeg', '-f', 'lavfi', '-i', 'color=black:size=64x64:duration=0.1',
                    '-c:v', 'libx264', '-y', test_input
                ], capture_output=True, timeout=10)
                
                if os.path.exists(test_input):
                    # Test NVIDIA AV1 encoder
                    if 'av1_nvenc' in encoders:
                        test_output = os.path.join(temp_dir, "test_nvenc.mp4")
                        result = subprocess.run([
                            'ffmpeg', '-i', test_input, '-c:v', 'av1_nvenc',
                            '-preset', 'p1', '-cq', '35', '-t', '0.1', '-y', test_output
                        ], capture_output=True, timeout=30)
                        if result.returncode == 0 and os.path.exists(test_output) and os.path.getsize(test_output) > 0:
                            self.hw_encoders['nvidia'] = True
                            logger.info("NVIDIA AV1 hardware encoder verified working")
                    
                    # Test AMD AV1 encoder  
                    if 'av1_amf' in encoders:
                        test_output = os.path.join(temp_dir, "test_amf.mp4")
                        result = subprocess.run([
                            'ffmpeg', '-i', test_input, '-c:v', 'av1_amf',
                            '-quality', 'speed', '-qp_i', '35', '-t', '0.1', '-y', test_output
                        ], capture_output=True, timeout=30)
                        if result.returncode == 0 and os.path.exists(test_output) and os.path.getsize(test_output) > 0:
                            self.hw_encoders['amd'] = True
                            logger.info("AMD AV1 hardware encoder verified working")
                    
                    # Test Intel QSV AV1 encoder
                    if 'av1_qsv' in encoders:
                        test_output = os.path.join(temp_dir, "test_qsv.mp4")
                        result = subprocess.run([
                            'ffmpeg', '-i', test_input, '-c:v', 'av1_qsv',
                            '-preset', 'veryfast', '-global_quality', '35', '-t', '0.1', '-y', test_output
                        ], capture_output=True, timeout=30)
                        if result.returncode == 0 and os.path.exists(test_output) and os.path.getsize(test_output) > 0:
                            self.hw_encoders['intel'] = True
                            logger.info("Intel AV1 hardware encoder verified working")
                        else:
                            logger.warning("Intel QSV AV1 encoder detected but not working properly")
                
        except Exception as e:
            logger.warning(f"Hardware encoder detection failed: {e}")
    
    def convert_to_av1(
        self, 
        input_path: str, 
        output_path: str, 
        quality: int = 30,
        speed: int = 6,
        progress_callback: Optional[Callable[[str], None]] = None,
        use_hardware: bool = True
    ) -> bool:
        """
        Convert video to AV1 format using FFmpeg with libaom-av1 encoder
        
        Args:
            input_path: Path to input video file
            output_path: Path to output AV1 video file
            quality: CRF quality (lower = better quality, 23-35 recommended)
            speed: Encoding speed preset (0-8, higher = faster but less efficient)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            if not os.path.exists(input_path):
                logger.error(f"Input file not found: {input_path}")
                return False
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Build FFmpeg command for AV1 conversion
            cmd = [self.ffmpeg_path, '-y', '-i', input_path]
            
            # Choose encoder based on hardware availability and preference
            if use_hardware and self.hw_encoders['nvidia']:
                # NVIDIA hardware encoder with reasonable settings
                cmd.extend([
                    '-c:v', 'av1_nvenc',
                    '-preset', 'p6',  # Faster preset to reduce CPU load
                    '-cq', str(quality),
                    '-multipass', '1',
                    '-spatial-aq', '1',
                    '-temporal-aq', '1',
                    '-gpu', '0'  # Use first GPU
                ])
                logger.info("Using NVIDIA hardware AV1 encoder")
            elif use_hardware and self.hw_encoders['amd']:
                # AMD hardware encoder with balanced settings
                cmd.extend([
                    '-c:v', 'av1_amf',
                    '-quality', 'speed',  # Prioritize speed over quality
                    '-qp_i', str(quality),
                    '-qp_p', str(quality + 2),
                    '-usage', 'transcoding'
                ])
                logger.info("Using AMD hardware AV1 encoder")
            elif use_hardware and self.hw_encoders['intel']:
                cmd.extend([
                    '-c:v', 'av1_qsv', 
                    '-preset', 'medium',
                    '-global_quality', str(quality)
                ])
                logger.info("Using Intel hardware AV1 encoder")
            else:
                # Fallback to software encoding - check availability
                svt_threads = max(1, multiprocessing.cpu_count() // 3)
                encoder_check = subprocess.run([self.ffmpeg_path, '-encoders'], 
                                             capture_output=True, text=True, timeout=5)
                
                if encoder_check.returncode == 0 and 'libsvtav1' in encoder_check.stdout:
                    # Use SVT-AV1 (faster)
                    cmd.extend([
                        '-c:v', 'libsvtav1',
                        '-crf', str(quality),
                        '-preset', '12'
                    ])
                    logger.info(f"Using SVT-AV1 software encoder with {svt_threads} threads")
                else:
                    # Fallback to libaom-av1 (slower but more compatible)
                    cmd.extend([
                        '-c:v', 'libaom-av1',
                        '-crf', str(quality),
                        '-cpu-used', '8',  # Fastest preset
                        '-row-mt', '1',    # Enable row-based multi-threading
                        '-tiles', f'{svt_threads}x1'  # Tile-based threading
                    ])
                    logger.info(f"Using libaom-av1 software encoder with {svt_threads} threads")
                
            # Common audio and threading settings - limit to 1/3 of CPU cores
            max_threads = max(1, multiprocessing.cpu_count() // 3)
            cmd.extend([
                '-c:a', 'libopus',
                '-b:a', '128k',
                '-threads', str(max_threads),  # Limit to 1/3 of available cores
                output_path
            ])
            
            logger.info(f"Using {max_threads} threads (1/3 of {multiprocessing.cpu_count()} available cores)")
            
            logger.info(f"Starting AV1 conversion: {input_path} -> {output_path}")
            
            # Log the command for debugging (truncate if too long)
            cmd_str = ' '.join(cmd)
            if len(cmd_str) > 200:
                cmd_str = cmd_str[:200] + '...'
            logger.info(f"FFmpeg command: {cmd_str}")
            
            # Check input file exists and is readable
            if not os.path.isfile(input_path):
                logger.error(f"Input file does not exist: {input_path}")
                return False
                
            file_size = os.path.getsize(input_path)
            logger.info(f"Input file size: {file_size / 1024 / 1024:.1f} MB")
            
            if progress_callback:
                progress_callback("Running")
            
            # Execute FFmpeg conversion with progress monitoring
            if progress_callback:
                # Use Popen for real-time progress monitoring
                process = subprocess.Popen(
                    cmd + ['-progress', 'pipe:1'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    universal_newlines=True
                )
                
                # Monitor progress in real-time
                self._monitor_progress(process, progress_callback)
                return_code = process.wait()
                
                # Create a simple object to hold the return code for consistency
                class ProcessResult:
                    def __init__(self, returncode):
                        self.returncode = returncode
                        self.stderr = "See logs for details"
                        
                process = ProcessResult(return_code)
                
            else:
                # Simple execution without progress monitoring
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout for conversion
                )
            
            if process.returncode == 0:
                logger.info(f"AV1 conversion successful: {output_path}")
                if progress_callback:
                    progress_callback("Completed")
                return True
            else:
                # Properly handle stderr output
                error_msg = process.stderr if isinstance(process.stderr, str) else "FFmpeg conversion failed"
                logger.error(f"AV1 conversion failed. Return code: {process.returncode}")
                logger.error(f"Error details: {error_msg}")
                if progress_callback:
                    progress_callback("Failed")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"AV1 conversion timed out for {input_path}")
            if progress_callback:
                progress_callback("Failed")
            return False
        except Exception as e:
            logger.error(f"Error during AV1 conversion: {e}")
            if progress_callback:
                progress_callback("Failed")
            return False
    
    def _monitor_progress(self, process, progress_callback):
        """Monitor FFmpeg progress and call callback with updates"""
        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                    
                line = line.strip()
                
                # Parse FFmpeg progress output
                if line.startswith('frame='):
                    # Extract progress info from FFmpeg output
                    parts = line.split()
                    frame_info = {}
                    
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            frame_info[key] = value
                    
                    if 'frame' in frame_info:
                        progress_callback(f"Processing frame {frame_info['frame']}")
                elif line.startswith('progress='):
                    if 'end' in line:
                        progress_callback("Conversion completed")
                        
        except Exception as e:
            logger.error(f"Progress monitoring error: {e}")


# Convenience function for easy import
def convert_video_to_av1(input_path: str, output_path: str, progress_callback: Optional[Callable[[str], None]] = None, ultra_fast: bool = False) -> bool:
    """
    Convenience function to convert a video to AV1 format
    
    Args:
        input_path: Path to input video
        output_path: Path to output video  
        progress_callback: Optional progress callback
        ultra_fast: Use ultra-fast conversion (lower quality, much faster)
    """
    converter = VideoConverter()
    if ultra_fast:
        return converter.convert_to_av1_ultra_fast(input_path, output_path, progress_callback)
    else:
        return converter.convert_to_av1(input_path, output_path, progress_callback)

def should_convert_video(video_path: str) -> bool:
    """
    Convenience function to check if a video should be converted to AV1
    """
    converter = VideoConverter()
    return converter.should_convert_to_av1(video_path)

class VideoConverterTester:
    """Test suite for video converter functionality"""
    
    def __init__(self):
        self.converter = VideoConverter()
    
    def test_conversion_with_timing(self, input_path: str, output_path: str, 
                                  time_limit: float = 300.0) -> dict:
        """
        Test AV1 conversion with detailed timing and progress reporting
        
        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            time_limit: Maximum time allowed for conversion (seconds)
            
        Returns:
            dict: Test results with timing, file sizes, codec info, etc.
        """
        import time
        
        results = {
            'success': False,
            'input_exists': False,
            'should_convert': False,
            'conversion_time': 0.0,
            'input_size': 0,
            'output_size': 0,
            'input_codec': None,
            'output_codec': None,
            'within_time_limit': False,
            'error_message': '',
            'progress_log': []
        }
        
        # Check if input file exists
        if not os.path.exists(input_path):
            results['error_message'] = f"Input file not found: {input_path}"
            return results
            
        results['input_exists'] = True
        results['input_size'] = os.path.getsize(input_path)
        results['input_codec'] = self.converter.check_codec(input_path)
        
        # Check if conversion is needed
        should_convert = self.converter.should_convert_to_av1(input_path)
        results['should_convert'] = should_convert
        
        if not should_convert:
            results['error_message'] = "Video doesn't need AV1 conversion"
            return results
        
        # Setup progress tracking
        start_time = time.time()
        
        def progress_callback(status):
            elapsed = time.time() - start_time
            progress_msg = f"Progress: {status} (elapsed: {elapsed:.1f}s)"
            results['progress_log'].append(progress_msg)
            if len(results['progress_log']) % 50 == 0:  # Log every 50th progress update
                logger.info(progress_msg)
        
        # Perform conversion
        try:
            success = self.converter.convert_to_av1_fast(
                input_path=input_path,
                output_path=output_path,
                progress_callback=progress_callback
            )
            
            end_time = time.time()
            results['conversion_time'] = end_time - start_time
            results['within_time_limit'] = results['conversion_time'] <= time_limit
            
            if success and os.path.exists(output_path):
                results['success'] = True
                results['output_size'] = os.path.getsize(output_path)
                results['output_codec'] = self.converter.check_codec(output_path)
            else:
                results['error_message'] = "Conversion completed but output file invalid"
                
        except Exception as e:
            results['error_message'] = f"Conversion failed with error: {str(e)}"
            results['conversion_time'] = time.time() - start_time
            
        return results
    
    def print_test_results(self, results: dict, input_path: str, output_path: str):
        """Print formatted test results"""
        print(f"\n=== AV1 Conversion Test Results ===")
        print(f"Input file: {os.path.basename(input_path)}")
        print(f"Output file: {os.path.basename(output_path)}")
        print(f"Input exists: {'✓' if results['input_exists'] else '✗'}")
        
        if results['input_exists']:
            print(f"Input size: {results['input_size'] / 1024 / 1024:.1f}MB")
            print(f"Input codec: {results['input_codec']}")
            print(f"Should convert: {'✓' if results['should_convert'] else '✗'}")
            
        if results['should_convert']:
            print(f"Conversion time: {results['conversion_time']:.1f}s")
            print(f"Within time limit: {'✓' if results['within_time_limit'] else '✗'}")
            
            if results['success']:
                print(f"Conversion: ✓ SUCCESS")
                print(f"Output size: {results['output_size'] / 1024 / 1024:.1f}MB")
                print(f"Output codec: {results['output_codec']}")
                compression_ratio = (1 - results['output_size'] / results['input_size']) * 100
                print(f"Compression: {compression_ratio:.1f}% size reduction")
            else:
                print(f"Conversion: ✗ FAILED")
                print(f"Error: {results['error_message']}")
        else:
            if results['error_message']:
                print(f"Skipped: {results['error_message']}")
        
        print("=" * 35)

def test_real_av1_conversion(input_path: str, output_path: str, time_limit: float = 300.0):
    """
    Convenience function to test AV1 conversion on real video files
    
    Args:
        input_path: Path to input video
        output_path: Path to output video  
        time_limit: Maximum conversion time in seconds (default: 5 minutes)
    """
    tester = VideoConverterTester()
    results = tester.test_conversion_with_timing(input_path, output_path, time_limit)
    tester.print_test_results(results, input_path, output_path)
    return results
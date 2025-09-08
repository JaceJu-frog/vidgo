# 调用代码示例：
import requests
from http import HTTPStatus
from dashscope.audio.asr import Recognition

def ms_to_srt_time(ms: int) -> str:
    """毫秒转为 SRT 时间格式 (HH:MM:SS,mmm)"""
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def json_to_word_srt(data: list) -> str:
    """
    把句级JSON转为逐字SRT字符串
    data: list of sentence dicts
    """
    srt_lines = []
    counter = 1

    for sentence in data:
        words = sentence.get("words", [])
        for word in words:
            start = ms_to_srt_time(word["begin_time"])
            end = ms_to_srt_time(word["end_time"])
            text = word["text"] + (word.get("punctuation") or "")
            
            srt_lines.append(f"{counter}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text.strip())
            srt_lines.append("")  # 空行分隔
            counter += 1

    return "\n".join(srt_lines)


def transcribe_audio_alibaba(audio_file_path: str, api_key: str, model: str = 'paraformer-realtime-v2') -> str:
    """
    使用阿里云DashScope进行音频转录
    
    Args:
        audio_file_path: 音频文件路径
        api_key: 阿里云API密钥
        model: 使用的模型，默认为paraformer-realtime-v2
        
    Returns:
        SRT格式的转录结果
    """
    import dashscope
    from dashscope.audio.asr import Recognition
    from http import HTTPStatus
    
    # 设置API密钥
    dashscope.api_key = api_key
    
    # 创建识别实例
    recognition = Recognition(
        model=model,
        format='mp3',
        sample_rate=16000,
        language_hints=['zh', 'en'],
        enable_words=True,
        enable_punctuation=True,
        callback=None,
    )
    
    # 执行识别
    result = recognition.call(audio_file_path)
    
    if result.status_code == HTTPStatus.OK:
        # 转换为SRT格式
        return json_to_word_srt(result.get_sentence())
    else:
        raise Exception(f'Alibaba ASR failed: {result.message}')

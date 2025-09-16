from openai import OpenAI
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=OPENAI_API_KEY,
    base_url="https://api.chatanywhere.tech/v1"
)



from openai import OpenAI

audio_file = open("./learning_how_to_learn.mp3", "rb")

transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file,
    response_format="verbose_json",  # Changed from "text" to "verbose_json"
    timestamp_granularities=["word"]  # This enables word-level timestamps
)

# Print the full transcription with word timestamps
print("Full transcription:")
print(transcription.text)
print("\nWord-level timestamps:")

def transcribe_audio_openai(audio_file_path: str, api_key: str, base_url: str = "https://api.openai.com/v1") -> str:
    """
    Transcribe audio using OpenAI Whisper API

    Args:
        audio_file_path: Path to audio file
        api_key: OpenAI API key
        base_url: API base URL

    Returns:
        Transcription result in SRT format
    """
    from openai import OpenAI
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
    
    # Convert to SRT format
    return _convert_whisper_to_srt(transcription.words)


def _convert_whisper_to_srt(words) -> str:
    """Convert OpenAI Whisper word-level timestamps to SRT format"""
    from utils.video.time_convert import seconds_to_srt_time
    
    srt_content = ""
    idx = 1
    
    for word in words:
        srt_content += f"{idx}\n{seconds_to_srt_time(word.start)} --> " \
                      f"{seconds_to_srt_time(word.end)}\n{word.word.strip()}\n\n"
        idx += 1
    
    return srt_content


# ===== Usage Example =====
# srt_output = transcribe_audio_openai("audio.mp3", "your_api_key")
# with open("output.srt", "w", encoding="utf-8") as f:
#     f.write(srt_output)

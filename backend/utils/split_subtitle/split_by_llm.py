import hashlib
import json
import os,math
import re
import sys
from typing import List, Optional
import openai
import logging
from utils.split_subtitle.cnt_tokens import count_words
from utils.split_subtitle.prompt import VIDEO_SPLIT_PROMPT_TEMPLATE 

# Add the project root to the path to import from video.views.set_setting
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from video.views.set_setting import load_all_settings

logger = logging.getLogger('subtitle_split')
if not logger.handlers:
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'subtitle_split.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

# 加载配置
# Load all settings and optionally disable proxies
settings = load_all_settings()
use_proxy = settings.get('DEFAULT', {}).get('use_proxy', 'true').lower() == 'true'
if not use_proxy:
    # disable HTTP(S) proxies for requests
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)

# 获取 API 配置
api_key = settings.get('DEFAULT', {}).get('api_key', '')
base_url = settings.get('DEFAULT', {}).get('base_url', 'https://api.deepseek.com')

# 常量定义
MODEL = "deepseek-chat"
CACHE_DIR = "cache"

# 初始化OpenAI客户端
client = openai.OpenAI(api_key=api_key, base_url=base_url)



def get_cache_key(text: str, model: str) -> str:
    """
    生成缓存键值
    """
    return hashlib.md5(f"{text}_{model}".encode()).hexdigest()

def get_cache(text: str, model: str) -> Optional[List[str]]:
    """
    从缓存中获取断句结果
    """
    cache_key = get_cache_key(text, model)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
    return None

def set_cache(text: str, model: str, result: List[str]) -> None:
    """
    将断句结果设置到缓存中
    """
    cache_key = get_cache_key(text, model)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
    except IOError:
        pass

def split_by_llm(text: str, use_cache: bool = False,max_length:int = 20,language:str= "en") -> List[str]:
    """
    使用LLM进行文本断句
    """
    # if use_cache:
    #     cached_result = get_cache(text, MODEL)
    #     if cached_result:
    #         print(f"[+] 从缓存中获取结果: {cached_result}")
    #         return cached_result
    word_limit=30 # max 
    SYSTEM_PROMPT = f"Use <br> for the split of paragraph"
    total_word_count = count_words(text)
    logger.info(f"total_word_count{total_word_count}")
    prompt = VIDEO_SPLIT_PROMPT_TEMPLATE.format(
        sentence=text
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        result = response.choices[0].message.content # 获取LLM返回的内容（OPENAI格式）
        # result = result[7:-3] # 清理结果中的多余```json和```
        json_data = json.loads(result)
        logger.info(f"[+] LLM返回结果: {json_data}")
        split_text = json_data[f'split']
        split_result = [segment.strip() for segment in split_text.split("<br>") if segment.strip()] # 将单个段落拆分为句子（各语言通用），通过strip去除文本两端的空格
        
        set_cache(text, MODEL, split_result)
        return split_result
    except Exception as e:
        print(f"[!] 请求LLM失败: {e}")
        return []

import re
from typing import List, Tuple, Set

def has_cjk_and_english(text: str) -> bool:
    """
    检查文本是否同时包含CJK字符（中文/日文/韩文）和英文字符
    
    Args:
        text: 要检查的文本
        
    Returns:
        布尔值，True表示同时包含CJK和英文字符
    """
    # CJK字符范围：
    # \u4e00-\u9fff: 中文汉字
    # \u3040-\u309f: 日文平假名
    # \u30a0-\u30ff: 日文片假名
    # \uac00-\ud7af: 韩文字符
    cjk_pattern = r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]'
    english_pattern = r'[a-zA-Z]'
    
    has_cjk = bool(re.search(cjk_pattern, text))
    has_english = bool(re.search(english_pattern, text))
    
    return has_cjk and has_english

class WordMerger:
    def __init__(self):
        """
        初始化词根合并器，尝试使用多种英文单词库
        """
        self.word_set = set()
        self.dict_source = ""
        
        # 按优先级尝试不同的单词库
        self._load_word_dict()
    
    def _load_word_dict(self):
        """
        尝试加载英文单词字典，按优先级使用不同的库
        """
        
        # 使用 pyspellchecker 库
        try:
            from spellchecker import SpellChecker
            spell = SpellChecker()
            self.word_set = spell.word_frequency.dictionary.keys()
            self.word_set = set(word.lower() for word in self.word_set)
            self.dict_source = "pyspellchecker"
            print(f"成功加载 pyspellchecker 库，包含 {len(self.word_set)} 个单词")
            return
        except ImportError:
            pass
        
        # 如果所有库都不可用，输出安装提示
        if not self.word_set:
            print("未找到可用的英文单词库，请安装以下任一库：")
            print("推荐: pip install english-words")
            print("或者: pip install nltk")
            print("或者: pip install pyspellchecker")
            print("\n正在使用最小化的备用词汇表...")
            self._load_minimal_words()
    
    def _load_minimal_words(self):
        """
        加载最小化的备用词汇表（仅在无法加载其他库时使用）
        """
        # 这只是一个很小的备用集合，建议安装上述库
        self.word_set = {
            'remote', 'github', 'repository', 'main', 'branch', 'commit',
            'config', 'clone', 'push', 'pull', 'merge', 'status', 'add',
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy'
        }
        self.dict_source = "minimal backup"
        print(f"使用备用词汇表，包含 {len(self.word_set)} 个单词")
    
    def is_valid_word(self, word: str) -> bool:
        """
        检查单词是否有效
        
        Args:
            word: 要检查的单词
            
        Returns:
            布尔值，表示单词是否有效
        """
        return word.lower() in self.word_set
    
    def find_english_fragments(self, text: str) -> List[Tuple[int, int, str]]:
        """
        找到文本中的英文片段及其位置
        
        Args:
            text: 输入文本
            
        Returns:
            包含(开始位置, 结束位置, 片段内容)的列表
        """
        # 匹配连续的英文字母（可能包含空格）
        pattern = r'[a-zA-Z]+(?:\s+[a-zA-Z]+)*'
        fragments = []
        
        for match in re.finditer(pattern, text):
            start, end = match.span()
            fragment = match.group()
            # 只处理包含空格的片段（被分割的单词）
            if ' ' in fragment:
                fragments.append((start, end, fragment))
        
        return fragments
    
    def try_merge_words(self, fragment: str, max_words: int = 4) -> str:
        """
        尝试合并英文片段中的单词
        
        Args:
            fragment: 英文片段
            max_words: 最大合并单词数
            
        Returns:
            合并后的文本
        """
        words = fragment.split()
        if len(words) <= 1:
            return fragment
        
        result = []
        i = 0
        
        while i < len(words):
            best_merge = words[i]
            best_length = 1
            
            # 尝试从当前位置开始合并2-max_words个单词
            for length in range(2, min(max_words + 1, len(words) - i + 1)):
                candidate = ''.join(words[i:i + length])
                if self.is_valid_word(candidate):
                    best_merge = candidate
                    best_length = length
            
            result.append(best_merge)
            i += best_length
        
        return ' '.join(result)
    
    def merge_text(self, text: str) -> str:
        """
        合并文本中被分割的英文单词
        只有当文本同时包含CJK字符（中文/日文/韩文）和英文字符时才进行合并
        
        Args:
            text: 输入文本
            
        Returns:
            处理后的文本
        """
        # 检查文本是否同时包含CJK和英文字符
        if not has_cjk_and_english(text):
            return text
        
        fragments = self.find_english_fragments(text)
        
        # 从后往前处理，避免位置偏移
        for start, end, fragment in reversed(fragments):
            merged = self.try_merge_words(fragment)
            text = text[:start] + merged + text[end:]
        
        return text

# 使用示例
def main():
    print("=== 英文词根合并工具 ===\n")
    
    # 初始化合并器
    merger = WordMerger()
    print(f"使用词典: {merger.dict_source}\n")
    
    # 测试文本
    test_texts = [
        "第一件事就是要把rem ote 仓库复制到本地",  # 中英混合，应该合并
        "也就是g it hub 叫做rem ote",              # 中英混合，应该合并
        "然后这个re p osit ory 的主分支是m ain",  # 中英混合，应该合并
        "我们需要con f ig 用户信息",               # 中英混合，应该合并
        "使用g it cl one 命令下载代码",            # 中英混合，应该合并
        "这是一个ex am ple 示例文本",             # 中英混合，应该合并
        "pro gram ming 是很有趣的",               # 中英混合，应该合并
        "上面只有一个commit 是in it",             # 中英混合，应该合并
        "rem ote rep osit ory",                  # 纯英文，不应该合并
        "this is an ex am ple",                  # 纯英文，不应该合并
        "这是纯中文句子",                         # 纯中文，不应该合并
        "Hello こんにちは"                        # 英文+日文，应该合并
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"原文 {i}: {text}")
        merged = merger.merge_text(text)
        print(f"处理后: {merged}")
        print()

if __name__ == "__main__":
    main()
    
    print("\n" + "="*50)
    print("推荐安装库的命令:")
    print("pip install english-words     # 最简单，推荐")
    print("pip install nltk              # 功能强大")
    print("pip install pyspellchecker    # 拼写检查功能")
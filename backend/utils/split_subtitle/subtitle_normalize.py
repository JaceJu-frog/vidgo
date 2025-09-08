import re
import unicodedata
from typing import List, Dict, Tuple
import copy

def is_cjk_char(char):
    """判断字符是否为CJK字符（中文、日文、韩文）"""
    if not char:
        return False
    
    code_point = ord(char)
    # CJK Unified Ideographs
    if 0x4E00 <= code_point <= 0x9FFF:
        return True
    # CJK Extension A
    if 0x3400 <= code_point <= 0x4DBF:
        return True
    # Hiragana
    if 0x3040 <= code_point <= 0x309F:
        return True
    # Katakana
    if 0x30A0 <= code_point <= 0x30FF:
        return True
    # Hangul Syllables
    if 0xAC00 <= code_point <= 0xD7AF:
        return True
    # Hangul Jamo
    if 0x1100 <= code_point <= 0x11FF:
        return True
    
    return False

def is_english_char(char):
    """判断字符是否为英文字母"""
    return char.isalpha() and ord(char) < 128

def is_english_punctuation(char):
    """判断字符是否为英文标点符号"""
    english_punct = ".,;:!?\"'()[]{}/-_+=*&^%$#@~`|\\<>"
    return char in english_punct

def is_digit(char):
    """判断字符是否为数字"""
    return char.isdigit()

def get_char_display_width(char):
    """获取单个字符的display宽度"""
    if is_cjk_char(char):
        return 1.75
    elif is_english_char(char) or is_digit(char):
        return 1.0
    elif char == ' ' or is_english_punctuation(char):
        return 0.5
    else:
        # 其他字符默认按英文处理
        return 1.0

def calculate_display_length(tokens):
    """计算token列表的display长度"""
    if not tokens:
        return 0
    
    total_width = 0
    
    for i, token in enumerate(tokens):
        # 计算token本身的宽度
        for char in token:
            total_width += get_char_display_width(char)
        
        # 判断是否需要在token后添加空格
        if i < len(tokens) - 1:  # 不是最后一个token
            if token:  # token不为空
                last_char = token[-1]
                # 如果以英文、数字或英文标点结尾，添加空格
                if is_english_char(last_char) or is_digit(last_char) or is_english_punctuation(last_char):
                    total_width += 0.5  # 空格占0.5格
    
    return total_width

def merge_elements(elem1, elem2):
    """合并两个元素"""
    merged = {
        "start_time": elem1["start_time"] + elem2["start_time"],
        "end_time": elem1["end_time"] + elem2["end_time"],
        "text": elem1["text"] + elem2["text"]
    }
    return merged

def split_element(elem, split_index):
    """在指定索引处分割元素"""
    elem1 = {
        "start_time": elem["start_time"][:split_index],
        "end_time": elem["end_time"][:split_index],
        "text": elem["text"][:split_index]
    }
    elem2 = {
        "start_time": elem["start_time"][split_index:],
        "end_time": elem["end_time"][split_index:],
        "text": elem["text"][split_index:]
    }
    return elem1, elem2

def find_best_split_point(elem):
    """找到最佳分割点"""
    n = len(elem["text"])
    if n <= 1:
        return n // 2
    
    # 在1/6到5/6之间寻找
    start_idx = max(1, n // 6)
    end_idx = min(n - 1, 5 * n // 6)
    
    max_time_diff = 0
    best_split_idx = -1
    
    for i in range(start_idx, end_idx + 1):
        # 计算与前一个token的时间差
        time_diff = elem["start_time"][i] - elem["end_time"][i - 1]
        if time_diff > max_time_diff:
            max_time_diff = time_diff
            best_split_idx = i
    
    # 如果没有找到合适的分割点或时间差太小
    if best_split_idx == -1 or max_time_diff < 0.05:
        best_split_idx = n // 2
    
    return best_split_idx

def normalize_display_length(data_list, min_display=10, max_display=60):
    """
    规范化列表中每个元素的display长度
    
    Args:
        data_list: 输入列表，每个元素包含start_time, end_time, text三个字段
        min_display: 最小display长度
        max_display: 最大display长度
    
    Returns:
        规范化后的列表
    """
    if not data_list:
        return []
    
    result = copy.deepcopy(data_list)
    
    # 第一步：处理过长的元素（分割）
    i = 0
    while i < len(result):
        elem = result[i]
        display_len = calculate_display_length(elem["text"])
        
        if display_len > max_display:
            # 需要分割
            split_idx = find_best_split_point(elem)
            elem1, elem2 = split_element(elem, split_idx)
            
            # 替换当前元素为分割后的两个元素
            result[i:i+1] = [elem1, elem2]
            # 不增加i，继续检查第一个分割后的元素
        else:
            i += 1
    
    # 第二步：处理过短的元素（合并）
    changed = True
    while changed:
        changed = False
        i = 0
        
        while i < len(result):
            elem = result[i]
            display_len = calculate_display_length(elem["text"])
            
            if display_len < min_display:
                # 需要合并
                # 计算与前后元素的时间差
                prev_time_diff = float('inf')
                next_time_diff = float('inf')
                
                if i > 0:
                    # 与前一个元素的时间差
                    prev_elem = result[i - 1]
                    prev_time_diff = elem["start_time"][0] - prev_elem["end_time"][-1]
                
                if i < len(result) - 1:
                    # 与后一个元素的时间差
                    next_elem = result[i + 1]
                    next_time_diff = next_elem["start_time"][0] - elem["end_time"][-1]
                
                # 选择时间差较小的进行合并
                if prev_time_diff <= next_time_diff and i > 0:
                    # 与前一个元素合并
                    merged = merge_elements(result[i - 1], elem)
                    result[i - 1:i + 1] = [merged]
                    changed = True
                    # 不增加i，因为列表长度减少了
                elif next_time_diff < prev_time_diff and i < len(result) - 1:
                    # 与后一个元素合并
                    merged = merge_elements(elem, result[i + 1])
                    result[i:i + 2] = [merged]
                    changed = True
                    # 不增加i，继续检查合并后的元素
                else:
                    # 无法合并（边界情况）
                    i += 1
            else:
                i += 1
    
    return result


# 测试用例
def create_test_cases():
    """创建测试用例"""
    test_cases = []
    
    # 测试用例1: 正常长度的元素
    test_case1 = [
        {
            "start_time": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
            "end_time": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
            "text": ["你", "好", "世", "界", "2024", "年", "快", "乐"]
        },
        {
            "start_time": [4.1, 4.6, 5.1, 5.6],
            "end_time": [4.6, 5.1, 5.6, 6.1],
            "text": ["Hello", "world", "123", "!"]
        }
    ]
    
    # 测试用例2: 需要合并的短元素
    test_case2 = [
        {
            "start_time": [0.0, 0.5],
            "end_time": [0.5, 1.0],
            "text": ["你", "好"]
        },
        {
            "start_time": [1.1, 1.6],
            "end_time": [1.6, 2.1],
            "text": ["世", "界"]
        },
        {
            "start_time": [2.2],
            "end_time": [2.7],
            "text": ["2024"]
        },
        {
            "start_time": [2.8, 3.3, 3.8],
            "end_time": [3.3, 3.8, 4.3],
            "text": ["Good", "morning", "!"]
        }
    ]
    
    # 测试用例3: 需要分割的长元素（超过60的display长度）
    test_case3 = [
        {
            "start_time": [i*0.5 for i in range(40)],
            "end_time": [(i+1)*0.5 for i in range(40)],
            "text": ["这", "是", "一", "个", "很", "长", "的", "中", "文", "句",
                    "子", "需", "要", "被", "分", "割", "成", "多", "个", "部",
                    "分", "因", "为", "它", "的", "display", "长", "度", "超", "过",
                    "了", "60", "个", "单", "位", "所", "以", "必", "须", "分"]
        },
        {
            "start_time": [(i+2)*0.5 for i in range(40)],
            "end_time": [(i+3)*0.5 for i in range(40)],
            "text": ["这", "是", "一", "个", "很", "长", "的", "中", "文", "句",
                    "子", "需", "要", "被", "分", "割", "成", "多", "个", "部",
                    "分", "因", "为", "它", "的", "display", "长", "度", "超", "过",
                    "了", "60", "个", "单", "位", "所", "以", "必", "须", "分"]
        }
    ]
    
    # 测试用例4: 混合中英文和数字
    test_case4 = [
        {
            "start_time": [0.0, 0.5, 1.0, 1.5],
            "end_time": [0.5, 1.0, 1.5, 2.0],
            "text": ["我", "love", "你", "365"]
        },
        {
            "start_time": [2.1, 2.6, 3.1, 3.6, 4.1],
            "end_time": [2.6, 3.1, 3.6, 4.1, 4.6],
            "text": ["Python", "3", "是", "最", "好"]
        },
        {
            "start_time": [4.7, 5.2, 5.7],
            "end_time": [5.2, 5.7, 6.2],
            "text": ["的", "100", "%"]
        }
    ]
    
    # 测试用例5: 包含大量数字的元素
    test_case5 = [
        {
            "start_time": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5],
            "end_time": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
            "text": ["第", "1", "章", "第", "2", "节"]
        },
        {
            "start_time": [3.1, 3.6, 4.1, 4.6, 5.1],
            "end_time": [3.6, 4.1, 4.6, 5.1, 5.6],
            "text": ["总", "共", "100", "页", "内容"]
        },
        {
            "start_time": [5.7, 6.2, 6.7, 7.2],
            "end_time": [6.2, 6.7, 7.2, 7.7],
            "text": ["2024", "年", "12", "月"]
        }
    ]
    
    return [test_case1, test_case2, test_case3, test_case4, test_case5]


# 测试函数
def test_normalize():
    """测试规范化功能"""
    test_cases = create_test_cases()
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*50}")
        print(f"测试用例 {i+1}:")
        print(f"{'='*50}")
        
        print("\n原始数据:")
        for j, elem in enumerate(test_case):
            display_len = calculate_display_length(elem["text"])
            print(f"  元素{j+1}: {elem['text']} (display长度: {display_len:.2f})")
        
        result = normalize_display_length(test_case, min_display=10, max_display=60)
        
        print("\n规范化后:")
        for j, elem in enumerate(result):
            display_len = calculate_display_length(elem["text"])
            print(f"  元素{j+1}: {elem['text']} (display长度: {display_len:.2f})")
            # 验证长度是否在规定范围内
            if display_len < 10:
                print(f"    ⚠️ 警告: 长度小于最小值10")
            elif display_len > 60:
                print(f"    ⚠️ 警告: 长度大于最大值60")


if __name__ == "__main__":
    test_normalize()
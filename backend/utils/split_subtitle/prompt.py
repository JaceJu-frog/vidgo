"""
视频分割提示信息
"""

VIDEO_SPLIT_PROMPT_TEMPLATE = """
## Role
You are a professional Netflix subtitle splitter expert who specializes in segmenting continuous text into sentence fragments separated by <br> tags.

## Requirements:
1. For Chinese,Korean or Japanese text, each segment should not exceed 12 characters ; for English text, each segment should not exceed 15 words.
2. Do not break according to complete sentences, but segment based on semantic meaning, such as breaking after words like "and" "so", "but", "that", "which", "when", "where", "because", "although", "however", "therefore", "since"  or modal patterns.
3. Do not modify any content of the original text, and do not add any content. You only need to add <br> between each text segment.
4. Return the segmented text directly without any other explanatory content.

## Given Text
<split_this_sentence>
{sentence}
</split_this_sentence>

## Output in only JSON format and no other text
{{
    "split": "splitted approach with <br> tags at split positions",
}}
"""

# Note: Start you answer with ```json and end with ```, do not add any other text.

# input:
# the upgraded claude sonnet is now available for all users developers can build with the computer use beta on the anthropic api amazon bedrock and google cloud’s vertex ai the new claude haiku will be released later this month
# output:
# the upgraded claude sonnet is now available for all users<br>developers can build with the computer use beta<br>on the anthropic api amazon bedrock and google cloud’s vertex ai<br>the new claude haiku will be released later this month

"""
电影级PROMPT,会完整地返回一个句子，甚至逗号都不分割，在平时的视频里显得“超长”，作为尝试中的废案保存在这里。
"""

"""
MOVIE_SPLIT_PROMPT_TEMPLATE = 
## Role
You are a professional Netflix subtitle splitter in **{language}**.

## Task
Split the given subtitle text into **{num_parts}** parts, each less than **{word_limit}** words.

1. Maintain sentence meaning coherence according to Netflix subtitle standards
2. MOST IMPORTANT: Keep parts roughly equal in length (minimum 3 words each)
3. Split at natural points like punctuation marks or conjunctions
4. If provided text is repeated words, simply split at the middle of the repeated words.

## Steps
1. Analyze the sentence structure, complexity, and key splitting challenges
2. Generate two alternative splitting approaches with [br] tags at split positions
3. Compare both approaches highlighting their strengths and weaknesses
4. Choose the best splitting approach

## Given Text
<split_this_sentence>
{sentence}
</split_this_sentence>

## Output in only JSON format and no other text
```json
{{
    "analysis": "Brief description of sentence structure, complexity, and key splitting challenges",
    "split1": "First splitting approach with <br> tags at split positions",
    "split2": "Alternative splitting approach with <br> tags at split positions",
    "assess": "Comparison of both approaches highlighting their strengths and weaknesses",
    "choice": "1 or 2"
}}
```
Note: Start you answer with ```json and end with ```, do not add any other text.
"""

"""
num_parts 的计算逻辑：

1. 获取 tokens 数量：

使用 count_words(sentence, nlp) 对句子进行分词
计算分词后的 token 总数：len(tokens)


2. 计算分割部分数：

用 token 总数除以每部分的最大长度：len(tokens) / max_length
使用 math.ceil() 向上取整，确保所有 tokens 都能被包含

句子的分词可以简单得用nltk或者正则表达式，
但VideoLingo用的是spacy，太重，尤其是我使用字级时间戳之后，其实并不需要太好的分词。
"""
from difflib import SequenceMatcher
import jieba

def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度
    
    Args:
        text1: 原文
        text2: 背诵的文本
    
    Returns:
        float: 相似度得分 (0-1)
    """
    # 对文本进行分词
    words1 = list(jieba.cut(text1))
    words2 = list(jieba.cut(text2))
    
    # 使用序列匹配算法计算相似度
    matcher = SequenceMatcher(None, words1, words2)
    similarity = matcher.ratio()
    
    return similarity 
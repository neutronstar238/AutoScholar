"""关键词扩展与中英翻译。

支持：
- 语言检测（中文/英文）
- 中文→英文学术术语翻译（字典映射 + LLM备选）
- 学术词库扩展（同义词、缩写）
- 关键词去重和规范化

Requirements: 2.1, 2.7
"""

from __future__ import annotations

from typing import List, Optional
from loguru import logger


# 学术词库：同义词和缩写扩展
ACADEMIC_THESAURUS = {
    "llm": ["large language model", "foundation model", "generative ai"],
    "nlp": ["natural language processing", "text mining", "language model"],
    "computer vision": ["image recognition", "visual understanding", "vision transformer"],
    "reinforcement learning": ["rl", "policy optimization", "decision making"],
    "deep learning": ["neural network", "deep neural network", "dnn"],
    "machine learning": ["ml", "statistical learning", "predictive modeling"],
    "transformer": ["attention mechanism", "self-attention", "bert", "gpt"],
    "gan": ["generative adversarial network", "adversarial training"],
    "cnn": ["convolutional neural network", "convnet"],
    "rnn": ["recurrent neural network", "lstm", "gru"],
}

# 中英学术术语映射
ZH_EN_MAP = {
    "人工智能": "artificial intelligence",
    "机器学习": "machine learning",
    "深度学习": "deep learning",
    "大语言模型": "large language model",
    "计算机视觉": "computer vision",
    "自然语言处理": "natural language processing",
    "强化学习": "reinforcement learning",
    "神经网络": "neural network",
    "卷积神经网络": "convolutional neural network",
    "循环神经网络": "recurrent neural network",
    "生成对抗网络": "generative adversarial network",
    "注意力机制": "attention mechanism",
    "迁移学习": "transfer learning",
    "联邦学习": "federated learning",
    "知识图谱": "knowledge graph",
    "推荐系统": "recommendation system",
    "图神经网络": "graph neural network",
    "多模态": "multimodal",
    "预训练": "pretraining",
    "微调": "fine-tuning",
}


def detect_language(text: str) -> str:
    """检测文本语言（中文或英文）。
    
    Args:
        text: 输入文本
        
    Returns:
        "zh" 表示中文，"en" 表示英文
    """
    return "zh" if any("\u4e00" <= ch <= "\u9fff" for ch in text) else "en"


async def translate_keyword_with_llm(keyword: str) -> Optional[str]:
    """使用LLM翻译中文学术术语为英文。
    
    Args:
        keyword: 中文关键词
        
    Returns:
        英文翻译结果，失败返回None
    """
    try:
        from .model_client import model_client
        
        messages = [
            {
                "role": "system",
                "content": "You are an academic translator. Translate Chinese academic terms to English. Return ONLY the English translation, no explanations."
            },
            {
                "role": "user",
                "content": f"Translate this Chinese academic term to English: {keyword}"
            }
        ]
        
        result = await model_client.chat_completion(
            messages=messages,
            temperature=0.3,  # 低温度以获得更确定的翻译
            max_tokens=50,
            use_fallback=True
        )
        
        if result and result.get("content"):
            translation = result["content"].strip().lower()
            logger.info(f"LLM翻译: {keyword} -> {translation}")
            return translation
            
    except Exception as e:
        logger.warning(f"LLM翻译失败: {keyword}, 错误: {e}")
    
    return None


def translate_keyword(keyword: str, use_llm: bool = False) -> str:
    """翻译关键词（中文→英文）。
    
    优先使用字典映射，可选使用LLM作为备选。
    
    Args:
        keyword: 输入关键词
        use_llm: 是否在字典未命中时使用LLM翻译
        
    Returns:
        翻译后的关键词（英文小写）
    """
    normalized = keyword.strip()
    
    if detect_language(keyword) == "zh":
        # 优先使用字典映射
        translated = ZH_EN_MAP.get(normalized, None)
        if translated:
            return translated.lower()
        
        # 字典未命中，返回原词（LLM翻译需要异步调用，在expand_keywords中处理）
        return normalized
    
    return normalized.lower()


async def expand_keywords_async(keywords: List[str], use_llm: bool = False) -> List[str]:
    """异步版本：翻译并扩展关键词，支持LLM翻译。
    
    Args:
        keywords: 输入关键词列表
        use_llm: 是否使用LLM翻译未知中文术语
        
    Returns:
        去重后的扩展关键词列表
    """
    expanded: List[str] = []

    for keyword in keywords:
        if not keyword or not keyword.strip():
            continue
        
        # 翻译关键词
        if detect_language(keyword) == "zh":
            # 优先使用字典
            translated = ZH_EN_MAP.get(keyword.strip(), None)
            if not translated and use_llm:
                # 字典未命中，尝试LLM翻译
                translated = await translate_keyword_with_llm(keyword)
            if not translated:
                # LLM也失败，使用原词
                translated = keyword.strip()
        else:
            translated = keyword.strip().lower()
        
        expanded.append(translated)

        # 扩展同义词和缩写
        thesaurus_key = translated.lower()
        if thesaurus_key in ACADEMIC_THESAURUS:
            expanded.extend(ACADEMIC_THESAURUS[thesaurus_key])

    # 去重并保持顺序
    unique = []
    seen = set()
    for term in expanded:
        lowered = term.lower().strip()
        if lowered and lowered not in seen:
            seen.add(lowered)
            unique.append(term)
    
    return unique


def expand_keywords(keywords: List[str]) -> List[str]:
    """同步版本：翻译并扩展关键词（仅使用字典映射）。
    
    Args:
        keywords: 输入关键词列表
        
    Returns:
        去重后的扩展关键词列表
    """
    expanded: List[str] = []

    for keyword in keywords:
        if not keyword or not keyword.strip():
            continue
        
        translated = translate_keyword(keyword, use_llm=False)
        expanded.append(translated)

        # 扩展同义词和缩写
        thesaurus_key = translated.lower()
        if thesaurus_key in ACADEMIC_THESAURUS:
            expanded.extend(ACADEMIC_THESAURUS[thesaurus_key])

    # 去重并保持顺序
    unique = []
    seen = set()
    for term in expanded:
        lowered = term.lower().strip()
        if lowered and lowered not in seen:
            seen.add(lowered)
            unique.append(term)
    
    return unique

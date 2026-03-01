"""关键词扩展与简易中英映射。"""

from __future__ import annotations

from typing import List


ACADEMIC_THESAURUS = {
    "llm": ["large language model", "foundation model", "generative ai"],
    "nlp": ["natural language processing", "text mining", "language model"],
    "computer vision": ["image recognition", "visual understanding", "vision transformer"],
    "reinforcement learning": ["rl", "policy optimization", "decision making"],
}

ZH_EN_MAP = {
    "人工智能": "artificial intelligence",
    "机器学习": "machine learning",
    "深度学习": "deep learning",
    "大语言模型": "large language model",
    "计算机视觉": "computer vision",
    "自然语言处理": "natural language processing",
    "强化学习": "reinforcement learning",
}


def detect_language(text: str) -> str:
    return "zh" if any("\u4e00" <= ch <= "\u9fff" for ch in text) else "en"


def translate_keyword(keyword: str) -> str:
    normalized = keyword.strip().lower()
    if detect_language(keyword) == "zh":
        return ZH_EN_MAP.get(keyword.strip(), keyword.strip())
    return normalized


def expand_keywords(keywords: List[str]) -> List[str]:
    """翻译并扩展关键词，返回去重后的关键词列表。"""
    expanded: List[str] = []

    for keyword in keywords:
        if not keyword or not keyword.strip():
            continue
        translated = translate_keyword(keyword)
        expanded.append(translated)

        thesaurus_key = translated.lower()
        if thesaurus_key in ACADEMIC_THESAURUS:
            expanded.extend(ACADEMIC_THESAURUS[thesaurus_key])

    unique = []
    seen = set()
    for term in expanded:
        lowered = term.lower().strip()
        if lowered and lowered not in seen:
            seen.add(lowered)
            unique.append(term)
    return unique

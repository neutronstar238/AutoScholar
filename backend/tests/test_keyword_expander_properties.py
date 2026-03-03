"""
Property-based tests for KeywordExpander.

Feature: search-and-recommendation-optimization
Tests Properties 6 and 7 from the design document.
"""

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import HealthCheck
from unittest.mock import AsyncMock, patch

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.utils.keyword_expander import (
    detect_language,
    translate_keyword,
    expand_keywords,
    expand_keywords_async,
    ZH_EN_MAP,
    ACADEMIC_THESAURUS
)


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating Chinese text (academic terms)
chinese_academic_terms = st.sampled_from(list(ZH_EN_MAP.keys()))

# Strategy for generating English text (academic terms)
english_academic_terms = st.sampled_from(
    list(ACADEMIC_THESAURUS.keys()) + 
    ["artificial intelligence", "quantum computing", "blockchain"]
)

# Strategy for generating mixed Chinese/English queries
mixed_query_strategy = st.one_of(
    chinese_academic_terms,
    english_academic_terms,
    st.lists(chinese_academic_terms, min_size=1, max_size=3).map(lambda x: " ".join(x)),
    st.lists(english_academic_terms, min_size=1, max_size=3).map(lambda x: " ".join(x))
)

# Strategy for generating keyword lists
keyword_list_strategy = st.lists(
    st.one_of(chinese_academic_terms, english_academic_terms),
    min_size=1,
    max_size=5
)


# ============================================================================
# Property 6: 跨语言查询翻译 (Cross-language Query Translation)
# ============================================================================

@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(chinese_term=chinese_academic_terms)
def test_property_6_chinese_detection(chinese_term):
    """
    **Validates: Requirements 2.1**
    
    Feature: search-and-recommendation-optimization, Property 6: 跨语言查询翻译
    
    For any search query containing Chinese characters, the KeywordExpander should
    detect the language as Chinese.
    
    Test Strategy:
    1. Take a Chinese academic term
    2. Detect its language
    3. Verify it's detected as "zh"
    """
    detected = detect_language(chinese_term)
    assert detected == "zh", (
        f"Chinese term '{chinese_term}' should be detected as 'zh', "
        f"but got '{detected}'"
    )


@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(english_term=english_academic_terms)
def test_property_6_english_detection(english_term):
    """
    **Validates: Requirements 2.1**
    
    Feature: search-and-recommendation-optimization, Property 6: 跨语言查询翻译
    
    For any search query containing only English characters, the KeywordExpander
    should detect the language as English.
    
    Test Strategy:
    1. Take an English academic term
    2. Detect its language
    3. Verify it's detected as "en"
    """
    detected = detect_language(english_term)
    assert detected == "en", (
        f"English term '{english_term}' should be detected as 'en', "
        f"but got '{detected}'"
    )


@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(chinese_term=chinese_academic_terms)
def test_property_6_chinese_translation_dictionary(chinese_term):
    """
    **Validates: Requirements 2.1**
    
    Feature: search-and-recommendation-optimization, Property 6: 跨语言查询翻译
    
    For any Chinese academic term in the dictionary, the KeywordExpander should
    translate it to the correct English term using dictionary mapping.
    
    Test Strategy:
    1. Take a Chinese term from ZH_EN_MAP
    2. Translate it using translate_keyword
    3. Verify the translation matches the expected English term
    """
    expected_translation = ZH_EN_MAP[chinese_term].lower()
    actual_translation = translate_keyword(chinese_term, use_llm=False)
    
    assert actual_translation == expected_translation, (
        f"Chinese term '{chinese_term}' should translate to '{expected_translation}', "
        f"but got '{actual_translation}'"
    )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(chinese_term=chinese_academic_terms)
async def test_property_6_chinese_in_expansion(chinese_term):
    """
    **Validates: Requirements 2.1**
    
    Feature: search-and-recommendation-optimization, Property 6: 跨语言查询翻译
    
    For any Chinese academic term, when expanded, the result should contain
    the English translation.
    
    Test Strategy:
    1. Take a Chinese term
    2. Expand it using expand_keywords
    3. Verify the English translation is in the expanded results
    """
    expanded = expand_keywords([chinese_term])
    expected_translation = ZH_EN_MAP[chinese_term].lower()
    
    # The expanded list should contain the English translation
    assert len(expanded) > 0, "Expansion should return at least one term"
    assert expected_translation in [term.lower() for term in expanded], (
        f"Expanded keywords for '{chinese_term}' should contain English translation "
        f"'{expected_translation}', but got: {expanded}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=50,  # Reduced because this involves mocking LLM
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(chinese_term=chinese_academic_terms)
async def test_property_6_llm_translation_fallback(chinese_term):
    """
    **Validates: Requirements 2.1**
    
    Feature: search-and-recommendation-optimization, Property 6: 跨语言查询翻译
    
    For any Chinese term, when LLM translation is enabled and dictionary lookup
    succeeds, the system should use the dictionary translation (LLM is backup).
    
    Test Strategy:
    1. Mock LLM to return a different translation
    2. Expand keywords with use_llm=True
    3. Verify dictionary translation is used (not LLM)
    """
    # Mock LLM to return a different translation
    mock_llm_translation = "llm_translated_term"
    
    with patch('app.utils.keyword_expander.translate_keyword_with_llm', 
               new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_llm_translation
        
        # Expand with LLM enabled
        expanded = await expand_keywords_async([chinese_term], use_llm=True)
        
        # Should use dictionary translation, not LLM
        expected_translation = ZH_EN_MAP[chinese_term].lower()
        assert expected_translation in [term.lower() for term in expanded], (
            f"Should use dictionary translation '{expected_translation}' "
            f"for known term '{chinese_term}'"
        )
        
        # LLM should NOT be called for known terms
        mock_llm.assert_not_called()


# ============================================================================
# Property 7: 查询扩展和合并 (Query Expansion and Merging)
# ============================================================================

@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(keywords=keyword_list_strategy)
def test_property_7_expansion_includes_originals(keywords):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Property 7: 查询扩展和合并
    
    For any list of keywords, the expanded result should include the translated
    versions of the original keywords.
    
    Test Strategy:
    1. Take a list of keywords (Chinese or English)
    2. Expand them
    3. Verify all original keywords (or their translations) are in the result
    """
    expanded = expand_keywords(keywords)
    
    # Verify expansion returns results
    assert len(expanded) > 0, "Expansion should return at least one keyword"
    
    # For each original keyword, verify it or its translation is in expanded
    for keyword in keywords:
        if detect_language(keyword) == "zh":
            # Chinese term should be translated
            expected = ZH_EN_MAP.get(keyword.strip(), keyword.strip()).lower()
        else:
            # English term should be normalized
            expected = keyword.strip().lower()
        
        expanded_lower = [term.lower() for term in expanded]
        assert expected in expanded_lower, (
            f"Original keyword '{keyword}' (or its translation '{expected}') "
            f"should be in expanded results: {expanded}"
        )


@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(english_term=st.sampled_from(list(ACADEMIC_THESAURUS.keys())))
def test_property_7_thesaurus_expansion(english_term):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Property 7: 查询扩展和合并
    
    For any English term in the academic thesaurus, the expanded result should
    include synonyms and related terms from the thesaurus.
    
    Test Strategy:
    1. Take a term that exists in ACADEMIC_THESAURUS
    2. Expand it
    3. Verify the result includes the original term and its synonyms
    """
    expanded = expand_keywords([english_term])
    expanded_lower = [term.lower() for term in expanded]
    
    # Should include the original term
    assert english_term.lower() in expanded_lower, (
        f"Expanded result should include original term '{english_term}'"
    )
    
    # Should include at least one synonym from thesaurus
    expected_synonyms = ACADEMIC_THESAURUS[english_term]
    found_synonyms = [syn for syn in expected_synonyms if syn.lower() in expanded_lower]
    
    assert len(found_synonyms) > 0, (
        f"Expanded result for '{english_term}' should include at least one synonym "
        f"from {expected_synonyms}, but got: {expanded}"
    )


@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(keywords=keyword_list_strategy)
def test_property_7_no_duplicates(keywords):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Property 7: 查询扩展和合并
    
    For any list of keywords, the expanded result should not contain duplicates
    (case-insensitive).
    
    Test Strategy:
    1. Expand a list of keywords
    2. Verify no duplicate terms exist (case-insensitive)
    """
    expanded = expand_keywords(keywords)
    
    # Convert to lowercase for duplicate checking
    expanded_lower = [term.lower().strip() for term in expanded]
    
    # Check for duplicates
    unique_terms = set(expanded_lower)
    assert len(expanded_lower) == len(unique_terms), (
        f"Expanded keywords should not contain duplicates. "
        f"Got {len(expanded_lower)} terms but only {len(unique_terms)} unique: {expanded}"
    )


@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(keywords=keyword_list_strategy)
def test_property_7_expansion_increases_coverage(keywords):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Property 7: 查询扩展和合并
    
    For any list of keywords, the expanded result should contain at least as many
    unique terms as the unique input terms (usually more due to synonyms and translations).
    
    Test Strategy:
    1. Count unique input keywords
    2. Expand them
    3. Verify expanded count >= unique input count
    """
    # Filter out empty keywords and get unique terms
    non_empty_keywords = [k.strip() for k in keywords if k and k.strip()]
    unique_input = list(set(non_empty_keywords))
    
    if not unique_input:
        # Skip if all keywords are empty
        return
    
    expanded = expand_keywords(unique_input)
    
    # Expansion should provide at least as many terms as unique input
    # (in practice, usually more due to synonyms)
    assert len(expanded) >= len(unique_input), (
        f"Expanded keywords should have at least as many terms as unique input. "
        f"Unique input: {unique_input} ({len(unique_input)} terms), "
        f"Expanded: {expanded} ({len(expanded)} terms)"
    )


@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    keywords=st.lists(
        st.one_of(chinese_academic_terms, english_academic_terms),
        min_size=1,
        max_size=3
    )
)
def test_property_7_mixed_language_expansion(keywords):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Property 7: 查询扩展和合并
    
    For any mixed list of Chinese and English keywords, the expansion should
    handle both languages correctly and merge results.
    
    Test Strategy:
    1. Create a mixed list of Chinese and English terms
    2. Expand them
    3. Verify all terms are translated/normalized correctly
    4. Verify no duplicates exist
    """
    expanded = expand_keywords(keywords)
    
    # Should have results
    assert len(expanded) > 0, "Expansion should return results for mixed languages"
    
    # All expanded terms should be in English (lowercase)
    for term in expanded:
        # Should not contain Chinese characters
        has_chinese = any("\u4e00" <= ch <= "\u9fff" for ch in term)
        assert not has_chinese, (
            f"Expanded term '{term}' should not contain Chinese characters. "
            f"All terms should be translated to English."
        )
    
    # No duplicates
    expanded_lower = [term.lower().strip() for term in expanded]
    unique_terms = set(expanded_lower)
    assert len(expanded_lower) == len(unique_terms), (
        f"Mixed language expansion should not produce duplicates: {expanded}"
    )


@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(keywords=st.lists(st.just(""), min_size=1, max_size=5))
def test_property_7_empty_keyword_handling(keywords):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Property 7: 查询扩展和合并
    
    For any list containing empty or whitespace-only keywords, the expansion
    should filter them out and not crash.
    
    Test Strategy:
    1. Create a list of empty/whitespace keywords
    2. Expand them
    3. Verify it returns an empty list without errors
    """
    expanded = expand_keywords(keywords)
    
    # Should return empty list for all-empty input
    assert expanded == [], (
        f"Empty keywords should result in empty expansion, but got: {expanded}"
    )


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(keywords=keyword_list_strategy)
async def test_property_7_async_expansion_equivalence(keywords):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Property 7: 查询扩展和合并
    
    For any list of keywords, the async expansion (without LLM) should produce
    the same results as the sync expansion.
    
    Test Strategy:
    1. Expand keywords using sync version
    2. Expand same keywords using async version (use_llm=False)
    3. Verify results are identical
    """
    sync_expanded = expand_keywords(keywords)
    async_expanded = await expand_keywords_async(keywords, use_llm=False)
    
    # Results should be identical
    assert sync_expanded == async_expanded, (
        f"Sync and async expansion should produce identical results.\n"
        f"Sync: {sync_expanded}\n"
        f"Async: {async_expanded}"
    )


# ============================================================================
# Integration Property: Cross-language + Expansion
# ============================================================================

@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(chinese_term=chinese_academic_terms)
def test_integration_chinese_expansion_with_synonyms(chinese_term):
    """
    **Validates: Requirements 2.1, 2.7**
    
    Feature: search-and-recommendation-optimization, Properties 6 & 7 Integration
    
    For any Chinese term that translates to an English term with synonyms in the
    thesaurus, the expansion should include both the translation and its synonyms.
    
    Test Strategy:
    1. Take a Chinese term
    2. Check if its English translation has synonyms in thesaurus
    3. If yes, verify expansion includes translation + synonyms
    """
    expanded = expand_keywords([chinese_term])
    expected_translation = ZH_EN_MAP[chinese_term].lower()
    
    # Should include the translation
    expanded_lower = [term.lower() for term in expanded]
    assert expected_translation in expanded_lower, (
        f"Should include translation '{expected_translation}' for '{chinese_term}'"
    )
    
    # If translation has synonyms, should include them too
    if expected_translation in ACADEMIC_THESAURUS:
        expected_synonyms = ACADEMIC_THESAURUS[expected_translation]
        found_synonyms = [syn for syn in expected_synonyms if syn.lower() in expanded_lower]
        
        assert len(found_synonyms) > 0, (
            f"Should include synonyms for '{expected_translation}': {expected_synonyms}, "
            f"but got: {expanded}"
        )

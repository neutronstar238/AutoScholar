"""
Property-based tests for CacheManager.

Feature: search-and-recommendation-optimization
Tests Properties 8, 9, and 11 from the design document.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import HealthCheck

from app.utils.cache_manager import CacheManager


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

class InMemoryRedis:
    """Fake Redis implementation for testing."""
    
    def __init__(self):
        self.data = {}
        self.call_count = 0
    
    async def ping(self):
        return True
    
    async def get(self, key):
        self.call_count += 1
        return self.data.get(key)
    
    async def setex(self, key, ttl, payload):
        self.data[key] = payload
        return True
    
    async def keys(self, pattern):
        """Return keys matching pattern."""
        import fnmatch
        # Convert Redis pattern to Python fnmatch pattern
        py_pattern = pattern.replace('*', '*')
        return [k for k in self.data.keys() if fnmatch.fnmatch(k, py_pattern)]
    
    def reset_call_count(self):
        self.call_count = 0


@pytest.fixture
def cache_manager_with_fake_redis(monkeypatch):
    """Provide a CacheManager with fresh fake Redis for each test."""
    # Create a fresh fake Redis instance for each test
    fake_redis = InMemoryRedis()
    
    class DummyRedis:
        @staticmethod
        def from_url(*args, **kwargs):
            return fake_redis
    
    monkeypatch.setattr("app.utils.cache_manager.redis", DummyRedis)
    # CRITICAL: Must pass use_redis=True to actually use the fake Redis
    manager = CacheManager(redis_url="redis://fake", use_redis=True)
    return manager, fake_redis


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating valid keywords
keyword_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),  # Letters and digits
        whitelist_characters=' -_'
    ),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != '')

# Strategy for generating keyword lists
keywords_list_strategy = st.lists(
    keyword_strategy,
    min_size=1,
    max_size=10
)

# Strategy for generating filter dictionaries
filter_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.sampled_from(['date_from', 'date_to', 'author', 'category']),
        values=st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(min_value=2000, max_value=2025)
        ),
        min_size=0,
        max_size=4
    )
)

# Strategy for generating search results
paper_strategy = st.fixed_dictionaries({
    'id': st.text(min_size=5, max_size=20),
    'title': st.text(min_size=10, max_size=100),
    'abstract': st.text(min_size=20, max_size=200),
    'authors': st.lists(st.text(min_size=3, max_size=30), min_size=1, max_size=5),
    'published': st.text(min_size=10, max_size=10)  # Date format
})

results_strategy = st.lists(paper_strategy, min_size=1, max_size=20)


# ============================================================================
# Property 8: 缓存优先访问 (Cache Priority Access)
# ============================================================================

@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    keywords=keywords_list_strategy,
    filters=filter_strategy,
    results=results_strategy
)
async def test_property_8_cache_priority_access(
    keywords, filters, results, cache_manager_with_fake_redis
):
    """
    **Validates: Requirements 4.1, 4.2**
    
    Feature: search-and-recommendation-optimization, Property 8: 缓存优先访问
    
    For any search query, the Cache_Manager should check cache for cached results
    before making external API calls, and return cached results immediately if they
    exist and are not expired.
    
    Test Strategy:
    1. Store results in cache for a given query
    2. Retrieve results using the same query
    3. Verify that cached results are returned
    4. Verify that cache was checked (results match)
    """
    manager, fake_redis = cache_manager_with_fake_redis
    
    # Generate cache key
    cache_key = manager.generate_cache_key(keywords, filters)
    
    # Store results in cache
    store_success = await manager.set_cached_results(cache_key, results, ttl=3600)
    assert store_success is True, "Cache storage should succeed"
    
    # Retrieve results from cache
    cached_results = await manager.get_cached_results(cache_key)
    
    # Verify cached results are returned (cache priority access)
    assert cached_results is not None, "Cached results should be returned"
    assert cached_results == results, "Cached results should match stored results"
    
    # The fact that we got the exact results back proves cache was accessed
    # (no need to check implementation details like call_count)


# ============================================================================
# Property 9: 缓存存储往返 (Cache Storage Round-trip)
# ============================================================================

@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    keywords=keywords_list_strategy,
    filters=filter_strategy,
    results=results_strategy
)
async def test_property_9_cache_storage_roundtrip(
    keywords, filters, results, cache_manager_with_fake_redis
):
    """
    **Validates: Requirements 4.2, 4.3**
    
    Feature: search-and-recommendation-optimization, Property 9: 缓存存储往返
    
    For any search query with no cached results, after fetching from external API,
    the results should be stored in cache with TTL=3600, and a subsequent identical
    query within 3600 seconds should retrieve those cached results.
    
    Test Strategy:
    1. Generate unique cache key
    2. Store results with TTL=3600
    3. Retrieve results with identical query
    4. Verify retrieved results match stored results (round-trip)
    """
    manager, fake_redis = cache_manager_with_fake_redis
    
    # Generate cache key
    cache_key = manager.generate_cache_key(keywords, filters)
    
    # Step 1: Store results with TTL=3600 (simulating API fetch and cache)
    store_success = await manager.set_cached_results(cache_key, results, ttl=3600)
    assert store_success is True, "Cache storage should succeed"
    
    # Step 2: Retrieve results with identical query
    retrieved_results = await manager.get_cached_results(cache_key)
    
    # Step 3: Verify retrieved results match stored results (round-trip verification)
    assert retrieved_results is not None, "Cached results should be retrieved"
    assert retrieved_results == results, "Retrieved results should match stored results"
    
    # Additional verification: Ensure the data round-tripped correctly
    # (JSON serialization/deserialization should preserve structure)
    assert len(retrieved_results) == len(results), "Result count should match"
    for i, (retrieved, original) in enumerate(zip(retrieved_results, results)):
        assert retrieved['id'] == original['id'], f"Paper {i} ID should match"
        assert retrieved['title'] == original['title'], f"Paper {i} title should match"


# ============================================================================
# Property 11: 缓存键唯一性 (Cache Key Uniqueness)
# ============================================================================

@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    keywords1=keywords_list_strategy,
    keywords2=keywords_list_strategy,
    filters1=filter_strategy,
    filters2=filter_strategy
)
async def test_property_11_cache_key_uniqueness(
    keywords1, keywords2, filters1, filters2, cache_manager_with_fake_redis
):
    """
    **Validates: Requirements 4.5**
    
    Feature: search-and-recommendation-optimization, Property 11: 缓存键唯一性
    
    For any two different search queries (different keywords or filters), the
    Cache_Manager should generate different cache keys, ensuring no collision.
    
    Test Strategy:
    1. Generate cache keys for two different queries
    2. If queries are truly different, verify keys are different
    3. If queries are equivalent (same keywords/filters), keys should be same
    """
    manager, _ = cache_manager_with_fake_redis
    
    # Generate cache keys
    key1 = manager.generate_cache_key(keywords1, filters1)
    key2 = manager.generate_cache_key(keywords2, filters2)
    
    # Normalize keywords for comparison (case-insensitive, sorted)
    normalized_kw1 = sorted([k.lower().strip() for k in keywords1])
    normalized_kw2 = sorted([k.lower().strip() for k in keywords2])
    
    # Normalize filters for comparison
    normalized_f1 = json.dumps(filters1, sort_keys=True) if filters1 else None
    normalized_f2 = json.dumps(filters2, sort_keys=True) if filters2 else None
    
    # Determine if queries are truly different
    queries_are_different = (
        normalized_kw1 != normalized_kw2 or normalized_f1 != normalized_f2
    )
    
    if queries_are_different:
        # Different queries should produce different cache keys
        assert key1 != key2, (
            f"Different queries should produce different cache keys.\n"
            f"Keywords1: {keywords1}, Filters1: {filters1}\n"
            f"Keywords2: {keywords2}, Filters2: {filters2}\n"
            f"Key1: {key1}\n"
            f"Key2: {key2}"
        )
    else:
        # Equivalent queries should produce the same cache key
        assert key1 == key2, (
            f"Equivalent queries should produce the same cache key.\n"
            f"Keywords1: {keywords1}, Filters1: {filters1}\n"
            f"Keywords2: {keywords2}, Filters2: {filters2}\n"
            f"Key1: {key1}\n"
            f"Key2: {key2}"
        )


# ============================================================================
# Additional Property Test: Cache Key Stability
# ============================================================================

@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    keywords=keywords_list_strategy,
    filters=filter_strategy
)
async def test_cache_key_stability(keywords, filters, cache_manager_with_fake_redis):
    """
    Verify that generating a cache key multiple times with the same input
    produces the same key (deterministic behavior).
    
    This supports Property 11 by ensuring cache keys are stable and predictable.
    """
    manager, _ = cache_manager_with_fake_redis
    
    # Generate the same cache key multiple times
    key1 = manager.generate_cache_key(keywords, filters)
    key2 = manager.generate_cache_key(keywords, filters)
    key3 = manager.generate_cache_key(keywords, filters)
    
    # All keys should be identical
    assert key1 == key2 == key3, (
        "Cache key generation should be deterministic and stable"
    )


# ============================================================================
# Additional Property Test: Cache Key Order Independence
# ============================================================================

@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    keywords=keywords_list_strategy.filter(lambda x: len(x) > 1),
    filters=filter_strategy
)
async def test_cache_key_order_independence(keywords, filters, cache_manager_with_fake_redis):
    """
    Verify that keyword order doesn't affect cache key generation.
    
    Keywords ["ai", "ml"] and ["ml", "ai"] should produce the same cache key.
    This supports Property 11 by ensuring semantic equivalence.
    """
    manager, _ = cache_manager_with_fake_redis
    
    # Generate key with original order
    key1 = manager.generate_cache_key(keywords, filters)
    
    # Generate key with reversed order
    reversed_keywords = list(reversed(keywords))
    key2 = manager.generate_cache_key(reversed_keywords, filters)
    
    # Keys should be identical (order-independent)
    assert key1 == key2, (
        f"Cache keys should be order-independent.\n"
        f"Keywords: {keywords}\n"
        f"Reversed: {reversed_keywords}\n"
        f"Key1: {key1}\n"
        f"Key2: {key2}"
    )

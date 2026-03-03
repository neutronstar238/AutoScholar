"""Debug script to test Property 20"""

import asyncio
from datetime import datetime
from app.engines.user_profile_manager import UserProfileManager
from app.storage.local_storage import local_storage


async def test_property_20_debug():
    """Debug test for Property 20"""
    
    user_id = 9000
    search_queries = ['00000']
    categories = ['cs.AI']
    
    profile_manager = UserProfileManager(max_keywords=20)
    
    # Clean up first
    all_interests = await local_storage._read_table("user_interests")
    cleaned = [row for row in all_interests if int(row.get('user_id', 0)) < 9000]
    await local_storage._write_table("user_interests", cleaned)
    
    all_history = await local_storage._read_table("search_history")
    cleaned = [row for row in all_history if int(row.get('user_id', 0)) < 9000]
    await local_storage._write_table("search_history", cleaned)
    
    # Create search history for user
    for query in search_queries:
        await local_storage.create_search_history({
            'user_id': user_id,
            'query': query,
            'result_count': 5,
            'source': 'primary',
            'created_at': datetime.utcnow().isoformat()
        })
    
    # Create reading behavior (interests from categories)
    for category in categories:
        created = await local_storage.create_user_interest({
            'user_id': user_id,
            'keyword': category.lower(),
            'weight': 0.3,
            'last_updated': datetime.utcnow().isoformat()
        })
        print(f"Created interest: {created}")
    
    # Check what's in storage
    stored_interests = await local_storage.get_user_interests(user_id, limit=10)
    print(f"\nStored interests for user {user_id}: {stored_interests}")
    
    # Extract interests automatically (no explicit interests parameter)
    extracted_interests = await profile_manager.extract_interests(user_id, limit=10)
    print(f"\nExtracted interests: {extracted_interests}")
    
    # Verify interests were extracted
    print(f"\nNumber of extracted interests: {len(extracted_interests)}")
    
    if len(extracted_interests) > 0:
        # Verify extracted interests are InterestKeyword objects
        for interest in extracted_interests:
            print(f"Interest: keyword={interest.keyword}, weight={interest.weight}")
        
        # Verify interests reflect user's categories
        extracted_keywords = [i.keyword for i in extracted_interests]
        category_keywords = [c.lower() for c in categories]
        
        print(f"\nExtracted keywords: {extracted_keywords}")
        print(f"Category keywords: {category_keywords}")
        
        # At least some categories should appear in extracted interests
        matching_categories = [k for k in extracted_keywords if k in category_keywords]
        print(f"Matching categories: {matching_categories}")
        
        if len(matching_categories) > 0:
            print("\n✅ TEST PASSED")
        else:
            print("\n❌ TEST FAILED: No matching categories")
    else:
        print("\n❌ TEST FAILED: No interests extracted")


if __name__ == "__main__":
    asyncio.run(test_property_20_debug())

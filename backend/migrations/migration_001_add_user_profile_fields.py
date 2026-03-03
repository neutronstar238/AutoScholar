"""
Migration: Add user profile fields to UserInterest and SearchHistory tables

This migration adds:
- last_updated field to user_interests table
- result_count and source fields to search_history table
- Makes user_id nullable in search_history to support anonymous users
"""

from sqlalchemy import text


async def upgrade(conn):
    """Apply migration"""
    
    # Add last_updated to user_interests
    await conn.execute(text("""
        ALTER TABLE user_interests 
        ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """))
    
    # Add result_count to search_history
    await conn.execute(text("""
        ALTER TABLE search_history 
        ADD COLUMN IF NOT EXISTS result_count INTEGER DEFAULT 0
    """))
    
    # Add source to search_history
    await conn.execute(text("""
        ALTER TABLE search_history 
        ADD COLUMN IF NOT EXISTS source VARCHAR(50)
    """))
    
    # Make user_id nullable in search_history (if not already)
    await conn.execute(text("""
        ALTER TABLE search_history 
        ALTER COLUMN user_id DROP NOT NULL
    """))
    
    print("Migration 001_add_user_profile_fields completed successfully")


async def downgrade(conn):
    """Rollback migration"""
    
    # Remove added columns
    await conn.execute(text("""
        ALTER TABLE user_interests 
        DROP COLUMN IF EXISTS last_updated
    """))
    
    await conn.execute(text("""
        ALTER TABLE search_history 
        DROP COLUMN IF EXISTS result_count
    """))
    
    await conn.execute(text("""
        ALTER TABLE search_history 
        DROP COLUMN IF EXISTS source
    """))
    
    # Make user_id NOT NULL again
    await conn.execute(text("""
        ALTER TABLE search_history 
        ALTER COLUMN user_id SET NOT NULL
    """))
    
    print("Migration 001_add_user_profile_fields rolled back successfully")

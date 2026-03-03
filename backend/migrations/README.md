# Database Migrations

This directory contains database migration scripts for the AutoScholar system.

## Running Migrations

### Upgrade (Apply migrations)

```bash
cd backend
python -m migrations.run_migrations upgrade
```

### Downgrade (Rollback migrations)

```bash
cd backend
python -m migrations.run_migrations downgrade
```

## Available Migrations

### 001: Add User Profile Fields

**File**: `migration_001_add_user_profile_fields.py`

**Changes**:
- Adds `last_updated` field to `user_interests` table
- Adds `result_count` field to `search_history` table
- Adds `source` field to `search_history` table
- Makes `user_id` nullable in `search_history` to support anonymous users

**Requirements**: 5.1, 5.2, 10.1

## Migration Structure

Each migration file should contain:
- `upgrade(conn)` - Function to apply the migration
- `downgrade(conn)` - Function to rollback the migration
- Documentation describing the changes

## Notes

- Migrations use raw SQL with SQLAlchemy's `text()` function
- All migrations are idempotent (can be run multiple times safely)
- Always test migrations on a development database first

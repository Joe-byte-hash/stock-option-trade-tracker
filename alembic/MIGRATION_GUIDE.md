# Database Migration Guide

This guide explains how to use Alembic to manage database schema changes for the Stock & Options Trade Tracker.

## Overview

We use Alembic for database migrations to:
- Add new columns to existing tables (e.g., the strategy column)
- Modify existing table structures
- Ensure existing user databases can be upgraded without data loss

## Running Migrations

### Upgrade to Latest Version

To upgrade your existing database to the latest schema:

```bash
# From the project root directory
alembic upgrade head
```

This will apply all pending migrations to your database.

### Specify Custom Database Path

By default, migrations use the database path in `alembic.ini` (./data/trades.db).

To migrate a different database:

```bash
# Temporarily set the database URL
alembic -x dbPath=/path/to/your/database.db upgrade head
```

### Check Current Version

To see which migration version your database is at:

```bash
alembic current
```

### View Migration History

To see all available migrations:

```bash
alembic history
```

## Available Migrations

### 3f1aabbd2713: Add Strategy Column to Trades

**Created:** 2025-10-24
**Purpose:** Adds the `strategy` column to the `trades` table for strategy tagging

**What it does:**
- Adds a new `strategy` column (VARCHAR(50), nullable)
- Sets default value to 'untagged' for all existing trades
- Allows users to tag trades with trading strategies

**To apply:**
```bash
alembic upgrade head
```

**To rollback:**
```bash
alembic downgrade -1
```

## Creating New Migrations

If you're developing a new feature that changes the database schema:

1. **Make changes to the model** in `src/trade_tracker/database/models.py`

2. **Create a new migration:**
   ```bash
   alembic revision -m "description_of_change"
   ```

3. **Edit the generated migration file** in `alembic/versions/` to add:
   - `upgrade()` function: SQL to apply the change
   - `downgrade()` function: SQL to revert the change

4. **Test the migration:**
   ```bash
   # Test upgrade
   alembic upgrade head

   # Test downgrade
   alembic downgrade -1

   # Re-upgrade
   alembic upgrade head
   ```

## Best Practices

1. **Always backup** your database before running migrations
2. **Test migrations** on a copy of your database first
3. **Never modify** migration files after they've been applied
4. **Run migrations** before starting the application after updating
5. **Check migration status** if you encounter database errors

## Troubleshooting

### Error: "Can't locate revision identified by 'head'"

This means Alembic can't find the migration history table. Run:
```bash
alembic stamp head
```

### Error: "Target database is not up to date"

Your database version doesn't match the migration files. Check current version:
```bash
alembic current
```

Then upgrade:
```bash
alembic upgrade head
```

### Error: "Table already exists"

The migration is trying to create a table that already exists. This might happen if:
- You manually created tables
- Migrations are out of sync

Solution: Mark the migration as applied without running it:
```bash
alembic stamp <revision_id>
```

## Example Workflow

### For New Users

New users don't need to run migrations. The application will create the database with the latest schema automatically.

### For Existing Users (Upgrading from Pre-Strategy Version)

If you have an existing database without the strategy column:

1. **Backup your database:**
   ```bash
   cp ./data/trades.db ./data/trades.db.backup
   ```

2. **Run the migration:**
   ```bash
   alembic upgrade head
   ```

3. **Verify the migration:**
   ```bash
   alembic current
   # Should show: 3f1aabbd2713 (head)
   ```

4. **Start the application:**
   ```bash
   python -m trade_tracker.visualization.dashboard
   ```

5. **Tag your trades** using the strategy dropdown in the trade history table

## Need Help?

If you encounter issues:
1. Check the migration logs for error messages
2. Verify your database path is correct
3. Ensure you have write permissions to the database file
4. See the main README for general troubleshooting

---

**Note:** This migration system is designed to be safe and reversible. You can always downgrade to a previous version if needed.

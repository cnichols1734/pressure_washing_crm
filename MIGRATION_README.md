# 🚀 AquaCRM SQLite to Supabase Migration

## Quick Start

### Step 1: Configure Your Supabase Connection

1. Open `supabase_config.py`
2. Replace the `DATABASE_URL` with your actual Supabase connection string
3. You can find this in your Supabase dashboard under **Settings > Database**
4. Copy the "URI" connection string

Example:
```python
DATABASE_URL = "postgresql://postgres:mypassword123@db.abcdefghijklmnop.supabase.co:5432/postgres"
```

### Step 2: Run the Migration

```bash
python run_migration.py
```

That's it! The script will:
- ✅ Test your Supabase connection
- ✅ Create a backup of your SQLite database
- ✅ Create all tables in PostgreSQL
- ✅ Migrate all your data (clients, quotes, invoices, payments, etc.)
- ✅ Verify the migration was successful
- ✅ Update your `.env` file to use Supabase
- ✅ Configure your app to use PostgreSQL

## What Gets Migrated

- **Clients**: All client information
- **Services**: Service definitions  
- **Quotes**: Quotes and quote items
- **Invoices**: Invoices and invoice items
- **Payments**: Payment records
- **Email Logs**: Email communication history

## Files Created

- `supabase_config.py` - Configuration file for your DATABASE_URL
- `run_migration.py` - Main migration script
- `app.db.backup_TIMESTAMP` - Automatic backup of your SQLite database
- Updated `.env` file with your Supabase DATABASE_URL

## Safety Features

- 🛡️ **Automatic Backup**: Your original SQLite database is backed up before migration
- 🔍 **Connection Testing**: Verifies Supabase connection before starting
- ✅ **Data Verification**: Compares record counts to ensure all data migrated
- 🔄 **Rollback Safe**: Your original database remains unchanged

## After Migration

1. **Restart your Flask app** - The app will now use Supabase PostgreSQL
2. **Test everything** - Make sure all features work correctly
3. **Remove SQLite files** - Once satisfied, you can delete the old database files

## Troubleshooting

If you get connection errors:
1. Check your DATABASE_URL in `supabase_config.py`
2. Verify your Supabase project is active
3. Ensure your password is correct
4. Check your network connection

## Rollback

To rollback to SQLite:
1. Remove the `DATABASE_URL` line from your `.env` file
2. Restart your Flask application
3. It will automatically use the SQLite database again 
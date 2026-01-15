# SQLite to Supabase PostgreSQL Migration Guide

This guide will help you migrate your AquaCRM application from SQLite to Supabase PostgreSQL.

## Prerequisites

1. **Supabase Account**: Make sure you have a Supabase project set up
2. **Database Password**: You'll need your Supabase database password
3. **Backup**: The migration script will create a backup, but consider making an additional manual backup

## Migration Process

### Step 1: Install Dependencies

First, install the PostgreSQL driver:

```bash
python install_dependencies.py
```

Or manually:
```bash
pip install psycopg2-binary==2.9.7
```

### Step 2: Prepare Your Supabase Database

1. Log into your Supabase dashboard
2. Go to Settings > Database
3. Note your database password (you'll need this for the migration)
4. Ensure your database is accessible (check connection pooling settings if needed)

### Step 3: Run the Migration

Execute the migration script:

```bash
python migrate_to_supabase.py
```

The script will:
1. Prompt for your Supabase database password
2. Test connections to both SQLite and PostgreSQL
3. Create a backup of your SQLite database
4. Create all tables in PostgreSQL
5. Migrate all data in the correct order (respecting foreign key constraints)
6. Verify the migration by comparing record counts
7. Optionally update your `.env` file

### Step 4: Update Configuration

If you didn't let the script update your `.env` file automatically, create or update it manually:

```bash
# .env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.urhejrvbaaxnkwcqvhur.supabase.co:5432/postgres
```

### Step 5: Test Your Application

1. Restart your Flask application
2. Test all functionality to ensure everything works correctly
3. Check that all your data is present and accessible

## What Gets Migrated

The migration script handles all your models:

- **Clients**: All client information
- **Services**: Service definitions
- **Quotes**: Quotes and quote items
- **Invoices**: Invoices and invoice items  
- **Payments**: Payment records
- **Email Logs**: Email communication history

## Migration Order

The script migrates data in the correct order to respect foreign key relationships:

1. Clients (no dependencies)
2. Services (no dependencies)
3. Quotes (depends on Clients)
4. Quote Items (depends on Quotes)
5. Invoices (depends on Clients, may reference Quotes)
6. Invoice Items (depends on Invoices)
7. Payments (depends on Invoices)
8. Email Logs (may reference various entities)

## Safety Features

- **Automatic Backup**: Creates a timestamped backup of your SQLite database
- **Connection Testing**: Verifies both database connections before starting
- **Batch Processing**: Commits data in batches to handle large datasets
- **Error Handling**: Continues migration even if individual records fail
- **Verification**: Compares record counts between source and destination
- **Rollback Protection**: Your original SQLite database remains unchanged

## Troubleshooting

### Connection Issues

If you get connection errors:

1. **Check Password**: Ensure your Supabase password is correct
2. **Network Access**: Verify you can reach Supabase from your network
3. **Database Status**: Check your Supabase project status in the dashboard

### Migration Errors

If specific records fail to migrate:

1. **Check Logs**: The script will show which records failed and why
2. **Data Integrity**: Some records might have data that doesn't fit PostgreSQL constraints
3. **Manual Review**: You may need to manually fix problematic records

### Performance

For large databases:

- The script processes data in batches of 100 records
- Migration time depends on your data size and network speed
- Consider running during off-peak hours for large datasets

## Post-Migration

### Verify Data Integrity

1. **Record Counts**: Check that all tables have the expected number of records
2. **Relationships**: Verify that foreign key relationships are intact
3. **Data Types**: Ensure all data types converted correctly
4. **Application Testing**: Test all application features thoroughly

### Clean Up (Optional)

After confirming everything works:

1. **Remove SQLite Files**: You can delete `app.db` and backup files
2. **Update Documentation**: Update any documentation that references SQLite
3. **Environment Variables**: Remove any SQLite-specific environment variables

## Environment Variables

After migration, your application will use these environment variables:

```bash
# Required
DATABASE_URL=postgresql://postgres:PASSWORD@db.urhejrvbaaxnkwcqvhur.supabase.co:5432/postgres

# Optional (for automated scripts)
SUPABASE_PASSWORD=your_password_here
```

## Benefits of PostgreSQL

After migration, you'll benefit from:

- **Scalability**: Better performance with larger datasets
- **Concurrent Access**: Multiple users can access the database simultaneously
- **Advanced Features**: JSON columns, full-text search, and more
- **Backup & Recovery**: Automated backups through Supabase
- **Real-time Features**: Potential for real-time updates
- **Cloud Hosting**: No need to manage database infrastructure

## Support

If you encounter issues:

1. Check the error messages in the migration script output
2. Verify your Supabase project settings
3. Ensure all dependencies are installed correctly
4. Review this guide for troubleshooting steps

## Rollback

If you need to rollback to SQLite:

1. Stop your application
2. Update your `.env` file to remove the `DATABASE_URL` (it will fall back to SQLite)
3. Restart your application
4. Your original SQLite database should still be intact

The migration script doesn't modify your original SQLite database, so rollback is always possible. 
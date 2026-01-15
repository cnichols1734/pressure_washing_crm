import sqlite3
import os
import re
from sqlite3 import Connection

# Database file
DB_FILE = 'app.db'
# Backup the database before making changes
BACKUP_FILE = 'app.db.bak'

def backup_database():
    """Create a backup of the database before making any changes"""
    if os.path.exists(DB_FILE):
        import shutil
        shutil.copy2(DB_FILE, BACKUP_FILE)
        print(f"Created backup at {BACKUP_FILE}")
    else:
        print(f"Database file {DB_FILE} not found")
        exit(1)

def get_tables(conn: Connection) -> list:
    """Get all tables from the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

def get_table_info(conn: Connection, table_name: str) -> list:
    """Get information about table columns"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def get_create_statement(conn: Connection, table_name: str) -> str:
    """Get the CREATE TABLE statement for a table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_schema WHERE type='table' AND name=?", (table_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_indices(conn: Connection, table_name: str) -> list:
    """Get all indices for a table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_schema WHERE type='index' AND tbl_name=? AND sql IS NOT NULL", (table_name,))
    return cursor.fetchall()

def get_foreign_keys(conn: Connection, table_name: str) -> list:
    """Get all foreign keys for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return cursor.fetchall()

def find_primary_key_column(conn: Connection, table_name: str) -> str:
    """Find the primary key column name for a table"""
    table_info = get_table_info(conn, table_name)
    for column in table_info:
        if column[5] == 1:  # pk flag is 1 for primary key
            return column[1]  # Return column name
    return None

def modify_create_statement(create_stmt: str, primary_key_column: str) -> str:
    """
    Modify the CREATE TABLE statement to add AUTOINCREMENT to INTEGER PRIMARY KEY
    
    This handles two formats:
    1. PRIMARY KEY (id) format
    2. INTEGER PRIMARY KEY format
    """
    if "AUTOINCREMENT" in create_stmt:
        return create_stmt
    
    # First check for the INTEGER PRIMARY KEY format
    if "INTEGER PRIMARY KEY" in create_stmt.upper():
        # Replace only the primary key column with AUTOINCREMENT
        pattern = fr"{primary_key_column}\s+INTEGER\s+PRIMARY KEY"
        return re.sub(pattern, f"{primary_key_column} INTEGER PRIMARY KEY AUTOINCREMENT", create_stmt, flags=re.IGNORECASE)
    
    # Next check for PRIMARY KEY (id) format
    pk_pattern = r'PRIMARY KEY\s*\(\s*([^)]+)\s*\)'
    pk_match = re.search(pk_pattern, create_stmt, re.IGNORECASE)
    
    if pk_match:
        pk_column = pk_match.group(1).strip()
        
        # Ensure we're modifying the correct column
        if pk_column == primary_key_column:
            # Check if column is defined as INTEGER
            # Use word boundaries to ensure we match the exact column name
            col_pattern = fr'\b{re.escape(primary_key_column)}\s+INTEGER\s+NOT NULL\b'
            col_match = re.search(col_pattern, create_stmt, re.IGNORECASE)
            
            if col_match:
                # Replace the column definition with INTEGER PRIMARY KEY AUTOINCREMENT
                modified = re.sub(
                    col_pattern, 
                    f'{primary_key_column} INTEGER PRIMARY KEY AUTOINCREMENT', 
                    create_stmt, 
                    flags=re.IGNORECASE
                )
                
                # Remove the PRIMARY KEY (column) part
                modified = re.sub(pk_pattern, '', modified, flags=re.IGNORECASE)
                
                # Clean up any extra commas that might be left
                modified = re.sub(r',\s*\)', ')', modified)
                modified = re.sub(r',\s*,', ',', modified)
                
                return modified
    
    return create_stmt

def add_autoincrement_to_tables():
    """Main function to add AUTOINCREMENT to all tables"""
    backup_database()
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = OFF")
    
    tables = get_tables(conn)
    modified_tables = []
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        for table_name in tables:
            create_stmt = get_create_statement(conn, table_name)
            
            # Skip if table doesn't have a CREATE statement or already has AUTOINCREMENT
            if not create_stmt or "AUTOINCREMENT" in create_stmt.upper():
                print(f"Skipping table {table_name}: already has AUTOINCREMENT or no CREATE statement")
                continue
            
            # Find the primary key column
            primary_key_column = find_primary_key_column(conn, table_name)
            
            if not primary_key_column:
                print(f"Skipping table {table_name}: could not find primary key column")
                continue
            
            # Check if primary key column is INTEGER type
            table_info = get_table_info(conn, table_name)
            pk_column_type = None
            
            for column in table_info:
                if column[1] == primary_key_column:
                    pk_column_type = column[2].upper()
                    break
            
            if not pk_column_type or 'INTEGER' not in pk_column_type:
                print(f"Skipping table {table_name}: primary key column '{primary_key_column}' is not INTEGER type")
                continue
            
            print(f"Processing table {table_name} (primary key: {primary_key_column})")
            
            # Get all indices for the table
            indices = get_indices(conn, table_name)
            
            # Modify the CREATE statement to add AUTOINCREMENT
            new_create_stmt = modify_create_statement(create_stmt, primary_key_column)
            
            print(f"Original create statement:\n{create_stmt}")
            print(f"Modified create statement:\n{new_create_stmt}")
            
            if create_stmt == new_create_stmt:
                print(f"No changes needed for table {table_name}")
                continue
            
            # Create a new table with the AUTOINCREMENT keyword
            temp_table_name = f"new_{table_name}"
            conn.execute(new_create_stmt.replace(f"CREATE TABLE {table_name}", f"CREATE TABLE {temp_table_name}"))
            
            # Copy data from the old table to the new table
            columns = [info[1] for info in get_table_info(conn, table_name)]
            columns_str = ", ".join(columns)
            
            conn.execute(f"INSERT INTO {temp_table_name} ({columns_str}) SELECT {columns_str} FROM {table_name}")
            
            # Drop the old table
            conn.execute(f"DROP TABLE {table_name}")
            
            # Rename the new table to the original name
            conn.execute(f"ALTER TABLE {temp_table_name} RENAME TO {table_name}")
            
            # Recreate indices
            for index in indices:
                if index[0]:  # Skip if None
                    conn.execute(index[0])
            
            modified_tables.append(table_name)
        
        conn.execute("COMMIT")
        print(f"Successfully added AUTOINCREMENT to {len(modified_tables)} tables: {', '.join(modified_tables)}")
    
    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"Error: {e}")
        print("Changes rolled back. Your database is unchanged.")
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

if __name__ == "__main__":
    add_autoincrement_to_tables() 
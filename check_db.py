import pymysql

def check_db_structure():
    """Check MySQL database structure."""
    try:
        conn = pymysql.connect(
            host='gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com',
            user='admin',
            password='87uW3y4oU59f',
            database='gpbible',
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # Show all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check key tables structure
        key_tables = ['users', 'bible-versions-user', 'denominations_user', 'user_preferences']
        
        for table_name in key_tables:
            if (table_name,) in tables:
                print(f"\n=== {table_name} table structure ===")
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]}")
                    
                # Show sample data
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                rows = cursor.fetchall()
                if rows:
                    print(f"  Sample data ({len(rows)} rows):")
                    for i, row in enumerate(rows):
                        print(f"    Row {i+1}: {row[:5]}...")  # First 5 columns only
            else:
                print(f"\n{table_name} table not found")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_db_structure()
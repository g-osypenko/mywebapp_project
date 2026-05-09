import argparse
import sys
import mariadb

def migrate():
    parser = argparse.ArgumentParser(description="Database Migration Tool")
    parser.add_argument("--db-host", type=str, default="127.0.0.1")
    parser.add_argument("--db-port", type=int, default=3306)
    parser.add_argument("--db-user", type=str, default="mywebapp")
    parser.add_argument("--db-pass", type=str, default="password")
    parser.add_argument("--db-name", type=str, default="mywebapp_db")
    args = parser.parse_args()

    try:
        conn = mariadb.connect(
            host=args.db_host,
            port=args.db_port,
            user=args.db_user,
            password=args.db_pass,
            database=args.db_name
        )
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                quantity INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);")
        
        conn.commit()
        print("Migration successful: Table 'items' is ready.")
        cur.close()
        conn.close()
    except mariadb.Error as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
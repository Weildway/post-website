import psycopg2
from werkzeug.security import generate_password_hash
import os

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"

def init_db():
    db = psycopg2.connect(  host=os.getenv('DB_HOST') or '127.0.0.1',
                            port=int(os.getenv('DB_PORT') or 5432),
                            user=os.getenv('POSTGRES_USER') or 'postgres',
                            password=os.getenv('POSTGRES_PASSWORD') or 'postgres',
                            database=os.getenv('POSTGRES_DB') or 'db'
                            )
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s;", (ADMIN_LOGIN,))
    user = cur.fetchone()
    if user is None:
        cur.execute(
            "INSERT INTO users(username, password, is_admin) VALUES (%s, %s, %s)",
            (   ADMIN_LOGIN,
                generate_password_hash(ADMIN_PASSWORD), 
                True
            )
        )
        db.commit()
    try:
        cur.execute(
            "INSERT INTO users(username, password, is_admin) VALUES (%s, %s, %s)",
            (   'test1',
                generate_password_hash('test1'), 
                False
            )
        )
        cur.execute(
            "INSERT INTO users(username, password, is_admin) VALUES (%s, %s, %s)",
            (   'test2',
                generate_password_hash('test2'), 
                False
            )
        )
    except:
        pass
    db.commit()
    cur.close()

if __name__ == "__main__":
    init_db()
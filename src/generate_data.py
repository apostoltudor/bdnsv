import json
import random
import time
from datetime import datetime
from faker import Faker
import psycopg2
from pymongo import MongoClient

# --- CONFIGURARE ---
# Folosim localhost pentru ca rulam scriptul de pe masina ta, catre Docker
PG_CONFIG = {
    "dbname": "shop_sql",
    "user": "admin",
    "password": "password123",
    "host": "localhost",
    "port": "5432"
}

MONGO_URI = "mongodb://admin:password123@localhost:27017/"

# Numar de date de generat
NUM_USERS = 100
NUM_PRODUCTS = 500 

fake = Faker()

def get_pg_connection():
    """Stabileste conexiunea la PostgreSQL cu retry logic."""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            return conn
        except Exception as e:
            print(f"⏳ Asteptam Postgres... ({e})")
            time.sleep(2)
            retries -= 1
    raise Exception("Nu s-a putut conecta la PostgreSQL!")

def init_sql_schema(cursor):
    """Creeaza tabelele in stil relational (Schema Rigida)."""
    # Tabel Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            city VARCHAR(50),
            created_at TIMESTAMP
        );
    """)
    
    # Tabel Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200),
            category VARCHAR(50),
            price DECIMAL(10, 2),
            description TEXT,
            specs JSONB  -- Aici trisam putin, Postgres stie JSON, dar il vom folosi limitat
        );
    """)
    
    # Tabel Orders (Relational - doar ID-uri)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            total_amount DECIMAL(10, 2),
            order_date TIMESTAMP
        );
    """)
    print("✅ Schema SQL creata (Tabele: users, products, orders).")

def generate_and_load():
    # 1. Conexiuni
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["shop_nosql"]
    
    # Curatam bazele de date vechi (pentru a putea rula scriptul de mai multe ori)
    init_sql_schema(pg_cur)
    pg_cur.execute("TRUNCATE users, products, orders RESTART IDENTITY CASCADE;")
    mongo_db["products"].drop()
    mongo_db["users"].drop()
    mongo_db["orders"].drop()

    print("🚀 Incepem generarea datelor...")

    # --- GENERARE PRODUSE ---
    products_data = []
    categories = ['Electronics', 'Clothing', 'Home', 'Books']
    
    print(f"   -> Generam {NUM_PRODUCTS} produse...")
    for _ in range(NUM_PRODUCTS):
        cat = random.choice(categories)
        item = {
            "name": f"{fake.word().title()} {fake.word().title()}",
            "category": cat,
            "price": round(random.uniform(10, 1000), 2),
            "description": fake.text(max_nb_chars=200),
            "specs": {
                "color": fake.color_name(),
                "weight": f"{random.randint(100, 2000)}g",
                "warranty": "2 years"
            }
        }
        products_data.append(item)

        # INSERT SQL (Normalize)
        pg_cur.execute("""
            INSERT INTO products (name, category, price, description, specs)
            VALUES (%s, %s, %s, %s, %s)
        """, (item['name'], item['category'], item['price'], item['description'], json.dumps(item['specs'])))

        # INSERT MONGO (Document - identic aici, dar structura e flexibila)
        mongo_db["products"].insert_one(item.copy())

    # --- GENERARE USERI ---
    users_data = []
    print(f"   -> Generam {NUM_USERS} useri...")
    for _ in range(NUM_USERS):
        user = {
            "name": fake.name(),
            "email": fake.email(),
            "city": fake.city(),
            "created_at": fake.date_time_this_year()
        }
        users_data.append(user)
        
        # SQL
        pg_cur.execute("""
            INSERT INTO users (name, email, city, created_at)
            VALUES (%s, %s, %s, %s)
        """, (user['name'], user['email'], user['city'], user['created_at']))
        
        # MONGO
        mongo_db["users"].insert_one(user.copy())

    # Commit SQL
    pg_conn.commit()
    
    # --- SALVARE DATASET (Cerință PDF) ---
    with open("dataset_initial.json", "w") as f:
        json.dump({"products": products_data, "users": [str(u) for u in users_data]}, f, default=str)
    
    print(f"✅ Gata! Datele au fost incarcate in Postgres si Mongo.")
    print(f"📁 Dataset salvat in 'dataset_initial.json' (pentru livrabil).")

    pg_cur.close()
    pg_conn.close()
    mongo_client.close()

if __name__ == "__main__":
    generate_and_load()
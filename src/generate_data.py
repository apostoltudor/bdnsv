import json
import random
import time
from datetime import datetime
from faker import Faker
import psycopg2
from pymongo import MongoClient

#configurare conexiune
PG_CONFIG = {
    "dbname": "shop_sql",
    "user": "admin",
    "password": "password123",
    "host": "localhost",
    "port": "5432"
}

MONGO_URI = "mongodb://admin:password123@localhost:27017/"

#numar de date de generat
NUM_USERS = 100
NUM_PRODUCTS = 500 

fake = Faker()

#generam produse folosind permutari inteligente de cuvinte
PRODUCT_TEMPLATES = {
    "Electronics": {
        "nouns": ["Laptop", "Smartphone", "Monitor", "Mouse", "Keyboard", "Headphones", "Tablet", "Smartwatch"],
        "adjectives": ["Pro", "Gaming", "Ultra", "Office", "Budget", "Wireless", "Ergonomic", "4K"],
        "descriptions": [
            "High performance device suitable for gaming and heavy work.",
            "Perfect for office work and productivity tasks.",
            "Budget friendly option with essential features.",
            "Premium quality build with latest technology.",
            "Compact and portable, ideal for travel."
        ]
    },
    "Clothing": {
        "nouns": ["T-Shirt", "Jeans", "Jacket", "Dress", "Sneakers", "Hat", "Scarf", "Gloves"],
        "adjectives": ["Cotton", "Leather", "Summer", "Winter", "Casual", "Elegant", "Vintage", "Slim-fit"],
        "descriptions": [
            "Comfortable and stylish, made from 100% organic materials.",
            "Perfect for casual outings or daily wear.",
            "Luxury item designed for special occasions.",
            "Durable and warm, ideal for cold weather.",
            "Lightweight and breathable design."
        ]
    },
    "Home": {
        "nouns": ["Lamp", "Chair", "Desk", "Sofa", "Rug", "Curtains", "Shelf", "Blender"],
        "adjectives": ["Modern", "Rustic", "Minimalist", "Smart", "Wooden", "Metal", "Cozy", "LED"],
        "descriptions": [
            "Adds a touch of elegance to your living room.",
            "Ergonomic design for maximum comfort.",
            "Smart home compatible device.",
            "Handcrafted from sustainable materials.",
            "Essential utility for every modern home."
        ]
    }
}

def get_pg_connection():
    """Stabileste conexiunea la PostgreSQL cu retry logic."""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            return conn
        except Exception as e:
            print(f"Asteptam Postgres... ({e})")
            time.sleep(2)
            retries -= 1
    raise Exception("Nu s-a putut conecta la PostgreSQL.")

def init_sql_schema(cursor):
    """Creeaza tabelele in stil relational."""
    #tabel Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            city VARCHAR(50),
            created_at TIMESTAMP
        );
    """)
    
    #tabel Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200),
            category VARCHAR(50),
            price DECIMAL(10, 2),
            description TEXT,
            specs JSONB
        );
    """)
    
    #tabel Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            total_amount DECIMAL(10, 2),
            order_date TIMESTAMP
        );
    """)

def generate_smart_product():
    #genereaza un produs folosind template-ul definit si pune un pret realist
    category = random.choice(list(PRODUCT_TEMPLATES.keys()))
    template = PRODUCT_TEMPLATES[category]
    
    noun = random.choice(template["nouns"])
    adj = random.choice(template["adjectives"])
    base_desc = random.choice(template["descriptions"])
    
    name = f"{adj} {noun} {fake.year()}"
    
    #adaugam context in descriere pt a ajuta modelul AI
    description = f"{base_desc} This {noun} is rated top tier in the {category} category."
    
    #calculul pretului pe baza cuvintelor din nume/descriere
    if "Luxury" in description or "Pro" in name:
        price = round(random.uniform(500, 3000), 2)
    elif "Budget" in name:
        price = round(random.uniform(20, 100), 2)
    else:
        price = round(random.uniform(50, 500), 2)
        
    return {
        "name": name,
        "category": category,
        "price": price,
        "description": description,
        "specs": {"color": fake.color_name(), "warranty": "2 years"}
    }

def generate_and_load():
    #stabilim conexiunile
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["shop_nosql"]
    
    #truncate
    init_sql_schema(pg_cur)
    pg_cur.execute("TRUNCATE users, products, orders RESTART IDENTITY CASCADE;")
    mongo_db["products"].drop()
    mongo_db["users"].drop()
    mongo_db["orders"].drop()

    print("Incepem generarea datelor...")

    #generare produse
    products_data = []
    print(f"   -> Generam {NUM_PRODUCTS} produse realiste...")
    for _ in range(NUM_PRODUCTS):
        item = generate_smart_product()
        products_data.append(item)

        #insert in sql
        pg_cur.execute("""
            INSERT INTO products (name, category, price, description, specs)
            VALUES (%s, %s, %s, %s, %s)
        """, (item['name'], item['category'], item['price'], item['description'], json.dumps(item['specs'])))

        #insert in mongo
        mongo_db["products"].insert_one(item.copy())

    #generare useri
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
        
        #insert SQL
        pg_cur.execute("""
            INSERT INTO users (name, email, city, created_at)
            VALUES (%s, %s, %s, %s)
        """, (user['name'], user['email'], user['city'], user['created_at']))
        
        #mongo insert
        mongo_db["users"].insert_one(user.copy())

    #commit SQL
    pg_conn.commit()
    
    #salvare dataset initial in JSON
    with open("dataset_initial.json", "w") as f:
        json.dump({"products": products_data, "users": [str(u) for u in users_data]}, f, default=str)
    
    print(f"Done! Datele sunt incarcate.")

    pg_cur.close()
    pg_conn.close()
    mongo_client.close()

if __name__ == "__main__":
    generate_and_load()
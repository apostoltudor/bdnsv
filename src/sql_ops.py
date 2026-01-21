import psycopg2
import time
import random
import json
from datetime import datetime

#configurare conexiune
PG_CONFIG = {
    "dbname": "shop_sql",
    "user": "admin",
    "password": "password123",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**PG_CONFIG)

def simulate_orders():
    """Generare comenzi fictive pentru a avea date de test pentru JOIN-uri"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Generare comenzi in SQL pentru a simula relatiile...")
    
    #stergem comenzile vechi si eliberam ID-urile
    cur.execute("TRUNCATE orders RESTART IDENTITY CASCADE;")
    
    #luam id-urile userilor si produselor existente
    cur.execute("SELECT id FROM users;")
    user_ids = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT id, price FROM products;")
    products = {row[0]: float(row[1]) for row in cur.fetchall()}
    product_ids = list(products.keys())

    #generam un numar de comenzi
    orders_batch = []
    for _ in range(2000):
        uid = random.choice(user_ids)
        #cate produse cumpara un user intr-o comanda
        num_items = random.randint(1, 5)
        selected_prods = random.sample(product_ids, num_items)
        
        total = sum(products[pid] for pid in selected_prods)
        
        #adaugam comanda in orders_batch
        orders_batch.append((uid, total, datetime.now()))

    #inseram comenzile in batch
    args_str = ','.join(cur.mogrify("(%s, %s, %s)", x).decode('utf-8') for x in orders_batch)
    cur.execute("INSERT INTO orders (user_id, total_amount, order_date) VALUES " + args_str)
    
    conn.commit()
    cur.close()
    conn.close()
    print("S-au generat comenzile in SQL.")

def benchmark_sql_query():
    """Masuram viteza unei interogari complexe cu join si agregari."""
    conn = get_db_connection()
    cur = conn.cursor()

    print("\nRulam Benchmark SQL (Complex Join)...")
    
    #Scenariu: Top 5 useri care au cheltuit cel mai mult, cu detalii despre oras
    #Interogarea necesita join intre tabele users si orders
    query = """
        SELECT u.name, u.city, COUNT(o.id) as total_orders, SUM(o.total_amount) as total_spent
        FROM users u
        JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name, u.city
        ORDER BY total_spent DESC
        LIMIT 5;
    """

    start_time = time.time()
    #executam de 10 ori ca sa facem o medie
    for _ in range(10):
        cur.execute(query)
        results = cur.fetchall()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10

    print(f"Rezultat SQL: {results[0]}")
    print(f"SQL Average Latency: {avg_time:.4f} secunde")
    
    cur.close()
    conn.close()
    return avg_time

if __name__ == "__main__":
    simulate_orders()
    benchmark_sql_query()
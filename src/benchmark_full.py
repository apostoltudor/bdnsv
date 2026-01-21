import time
import matplotlib.pyplot as plt
import psycopg2
from pymongo import MongoClient
import random

PG_CONFIG = {
    "dbname": "shop_sql",
    "user": "admin",
    "password": "password123",
    "host": "localhost",
    "port": "5432"
}
MONGO_URI = "mongodb://admin:password123@localhost:27017/"

def get_pg_conn():
    return psycopg2.connect(**PG_CONFIG)

def get_mongo_db():
    return MongoClient(MONGO_URI)["shop_nosql"]

#testele simple
def test_simple_sql(cur, target_ids):
    start = time.time()
    for pid in target_ids:
        cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
        _ = cur.fetchone()
    end = time.time()
    return (end - start) / len(target_ids) #latency pentru interogare simpla

def test_simple_mongo(db, target_ids):
    start = time.time()
    products_coll = db.products
    real_ids = [doc["_id"] for doc in products_coll.find().limit(len(target_ids))]
    
    start = time.time()
    for pid in real_ids:
        _ = products_coll.find_one({"_id": pid})
    end = time.time()
    return (end - start) / len(target_ids)

#testele agregate
def test_aggregate_sql(cur):
    query = """
        SELECT u.city, SUM(o.total_amount) 
        FROM users u 
        JOIN orders o ON u.id = o.user_id 
        GROUP BY u.city 
        ORDER BY SUM(o.total_amount) DESC 
        LIMIT 5;
    """
    start = time.time()
    cur.execute(query)
    _ = cur.fetchall()
    end = time.time()
    return end - start

def test_aggregate_mongo(db):
    pipeline = [
        {"$group": {"_id": "$user_city_snapshot", "total": {"$sum": "$total_amount"}}},
        {"$sort": {"total": -1}},
        {"$limit": 5}
    ]
    start = time.time()
    _ = list(db.orders.aggregate(pipeline))
    end = time.time()
    return end - start

def run_benchmark():
    print("Pornim benchmark complet (Simple vs Aggregate)...")
    
    #Setup SQL
    pg_conn = get_pg_conn()
    pg_cur = pg_conn.cursor()
    
    #Setup Mongo
    mongo_db = get_mongo_db()
    
    #pregatim 1000 de date de test si luam 500 de id-uri
    target_ids = [random.randint(1, 500) for _ in range(1000)]
    
    print("   -> Testam simple queries...")
    sql_simple_time = test_simple_sql(pg_cur, target_ids)
    mongo_simple_time = test_simple_mongo(mongo_db, target_ids)
    
    print("   -> Testam aggregate queries...")
    sql_agg_time = test_aggregate_sql(pg_cur)
    mongo_agg_time = test_aggregate_mongo(mongo_db)
    
    pg_cur.close()
    pg_conn.close()
    
    print("\nREZULTATE FINALE:")
    print(f"   SQL Simple Latency:   {sql_simple_time:.6f} sec")
    print(f"   Mongo Simple Latency: {mongo_simple_time:.6f} sec")
    print(f"   SQL Aggregate Time:   {sql_agg_time:.6f} sec")
    print(f"   Mongo Aggregate Time: {mongo_agg_time:.6f} sec")
    
    #generare grafic
    labels = ['Simple Query (Latency)', 'Complex Aggregation (Total Time)']
    sql_times = [sql_simple_time * 1000, sql_agg_time * 1000] #convertim in ms pentru vizibilitate
    mongo_times = [mongo_simple_time * 1000, mongo_agg_time * 1000]
    
    x = range(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar([i - width/2 for i in x], sql_times, width, label='PostgreSQL', color='#336791')
    rects2 = ax.bar([i + width/2 for i in x], mongo_times, width, label='MongoDB', color='#47A248')
    
    ax.set_ylabel('Timp de executie (milisecunde)')
    ax.set_title('Performanta SQL vs NoSQL (Simple vs Aggregate)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    
    ax.bar_label(rects1, padding=3, fmt='%.2f ms')
    ax.bar_label(rects2, padding=3, fmt='%.2f ms')
    
    plt.margins(y=0.1)
    
    plt.savefig('benchmark_results.png')
    print("\nGraficul a fost salvat ca 'benchmark_results.png'")

if __name__ == "__main__":
    run_benchmark()
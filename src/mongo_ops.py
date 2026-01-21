import time
import random
from datetime import datetime
from pymongo import MongoClient

MONGO_URI = "mongodb://admin:password123@localhost:27017/"

def get_mongo_db():
    #stabilim conexiunea la shop_nosql, altfel o creeaza
    client = MongoClient(MONGO_URI)
    return client["shop_nosql"]

def simulate_mongo_orders():
    db = get_mongo_db()
    
    print("Generare comenzi in MongoDB...")
    
    #ca un truncate, stergem comenzile vechi
    db.orders.drop()
    
    #ca un select
    users = list(db.users.find({}, {"_id": 1, "name": 1, "city": 1}))
    products = list(db.products.find({}, {"_id": 1, "name": 1, "price": 1}))
    
    orders_batch = []
    
    #generam comenzi
    for _ in range(2000):
        user = random.choice(users)
        
        num_items = random.randint(1, 5)
        selected_prods = random.sample(products, num_items)
        



        #in loc de un tabel relational, folosim un dictionar pt comenzi
        items_list = []
        total = 0
        for p in selected_prods:
            p_price = float(p["price"])
            items_list.append({
                "product_id": p["_id"],
                "name": p["name"],
                "price": p_price
            })
            total += p_price
            
        #documentul comenzii cu embedding si salvam snapshot user
        order_doc = {
            "user_id": user["_id"],
            "user_name_snapshot": user["name"], 
            "user_city_snapshot": user["city"],
            "items": items_list,
            "total_amount": total,
            "order_date": datetime.now()
        }
        orders_batch.append(order_doc)
    
    #le inseram pe toate odata
    db.orders.insert_many(orders_batch)
    print("S-au generat comenzile in MongoDB.")

def benchmark_mongo_query():
    db = get_mongo_db()
    print("\nRulam Benchmark pentru MongoDB...")
    
    #Scenariu: Top 5 useri care au cheltuit cel mai mult, cu detalii despre oras
    #Folosim agregari cu pipeline
    pipeline = [
        #grupam dupa id, calculam suma si luam datele din snapshot
        {
            "$group": {
                "_id": "$user_id",
                "total_spent": {"$sum": "$total_amount"},
                "total_orders": {"$sum": 1},
                "city": {"$first": "$user_city_snapshot"},
                "name": {"$first": "$user_name_snapshot"}
            }
        },
        #ordonam descrescator dupa totalul cheltuit
        {
            "$sort": {"total_spent": -1}
        },
        #ii luam doar pe primii 5
        {
            "$limit": 5
        }
    ]

    start_time = time.time()
    
    #Rulam de 10 ori pentru a face o medie
    for _ in range(10):
        results = list(db.orders.aggregate(pipeline))
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10

    print(f"Rezultat Mongo: {results[0]['name']} - {results[0]['total_spent']}")
    print(f"Mongo Average Latency: {avg_time:.4f} secunde")
    
    return avg_time

if __name__ == "__main__":
    simulate_mongo_orders()
    benchmark_mongo_query()
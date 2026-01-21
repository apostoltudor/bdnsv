import time
import random
import psycopg2
from pymongo import MongoClient
from pymongo.errors import PyMongoError

PG_CONFIG = {
    "dbname": "shop_sql",
    "user": "admin",
    "password": "password123",
    "host": "localhost",
    "port": "5432"
}
MONGO_URI = "mongodb://admin:password123@localhost:27017/"

def test_connection_loop():
    print("   -> Scriptul va incerca sa scrie date in fiecare secunda.")
    print("   -> Introdu in alt terminal 'docker stop bdnv_mongo' pentru a simula o cadere.")
    print("-----------------------------------------------------------------------")
    
    counter = 1
    
    while True:
        timestamp = time.strftime("%H:%M:%S")
        status_sql = "UNKNOWN"
        status_mongo = "UNKNOWN"
        
        #testam sql
        try:
            conn = psycopg2.connect(**PG_CONFIG, connect_timeout=1)
            cur = conn.cursor()
            cur.execute("SELECT 1;") #ping
            conn.close()
            status_sql = "ONLINE"
        except Exception as e:
            status_sql = "DOWN (Connection Refused)"

        #testam mongo
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
            db = client["shop_nosql"]
            #incercare insert
            db.chaos_logs.insert_one({"ping": counter, "time": timestamp})
            status_mongo = "ONLINE"
        except PyMongoError as e:
            status_mongo = "DOWN (Node Failure)"
            
        #afisam status live
        print(f"[{timestamp}] Iteratia {counter}: SQL=[{status_sql}] | MONGO=[{status_mongo}]")
        
        counter += 1
        time.sleep(1) 

if __name__ == "__main__":
    try:
        test_connection_loop()
    except KeyboardInterrupt:
        print("\nTest oprit.")
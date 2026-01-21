import time
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient

#all-MiniLM-L6-v2 este un model mic, rapid, de la Google/Microsoft
#transforma textul intr-un vector de 384 de dimensiuni
QDRANT_URI = "http://localhost:6333"
MONGO_URI = "mongodb://admin:password123@localhost:27017/"
MODEL_NAME = 'all-MiniLM-L6-v2'

def get_mongo_products():
    client = MongoClient(MONGO_URI)
    db = client["shop_nosql"]
    #extragem datele din bd mongo
    return list(db.products.find({}, {"name": 1, "description": 1, "price": 1}).limit(100))

def setup_vector_db():
    print("Incarcam modelul AI...")
    #descarca modelul
    encoder = SentenceTransformer(MODEL_NAME)
    
    client = QdrantClient(url=QDRANT_URI)
    
    collection_name = "products_semantic_search"
    
    #recreem colectia in Qdrant
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
        #Distance.COSINE ca sa calculam asemanarea folosind cosinusul dintre vectori
    )
    
    print("Colectia Qdrant a fost creata.")
    return client, encoder, collection_name

def index_data():
    client, encoder, collection_name = setup_vector_db()
    products = get_mongo_products()
    
    print(f"Vectorizam {len(products)} produse...")
    
    points = []
    for idx, prod in enumerate(products):
        #combinam numele si descrierea pentru embedding
        text_to_embed = f"{prod['name']}: {prod.get('description', '')}"
        
        #introducem textul in modelul pentru a obtine vector
        vector = encoder.encode(text_to_embed).tolist()
        
        #in qdrant salvam vectorul impreauna cu datele produsului
        points.append(models.PointStruct(
            id=idx,
            vector=vector,
            payload={
                "name": prod["name"],
                "price": prod["price"],
                "desc": prod.get("description", "")[:50] + "..."
            }
        ))

    #upload in qdrant
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    print("Produsele au fost indexate in Vector DB.")
    return client, encoder, collection_name

def semantic_search(query_text):
    #conectare la qdrant si incarcam modelul
    client = QdrantClient(url=QDRANT_URI)
    encoder = SentenceTransformer(MODEL_NAME)
    collection_name = "products_semantic_search"

    print(f"\nCautare semantica pentru: '{query_text}'")
    
    #convertim intrebarea in vector
    query_vector = encoder.encode(query_text).tolist()
    
    start_time = time.time()
    
    #calculcam cei mai apropiati vectori
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=3 #cei mai apropiati 3 vectori
    )
    
    end_time = time.time()
    
    print(f"Timp cautare: {end_time - start_time:.4f} secunde")
    print("Rezultate:")
    for result in search_result:
        #procentul de asemanare (1-distanta cosinus; 1 inseamna identic)
        print(f" - [Score: {result.score:.3f}] {result.payload['name']}")
        print(f"   Desc: {result.payload['desc']}")
        print(f"   Price: {result.payload['price']} RON\n")
        
if __name__ == "__main__":
    #indexam datele
    index_data()
    
    #testam o cautare care nu contine cuvinte cheie exacte
    #ex: cautam "luxury" dar produsele poate nu au cuvantul "luxury" in titlu, ci doar un pret mare
    semantic_search("cheap device for office work")
    semantic_search("luxury item expensive")
T2 – Relational vs. NoSQL

1. Project Description

This project implements a technical experiment to compare two database paradigms using a simulated E-commerce scenario (Users, Products, Orders). The objective is to analyze data modeling differences, query performance, and system reliability.

The project focuses on:
  - Data Modeling: Comparing normalized SQL schemas against embedded NoSQL documents.
  - Performance Benchmarking: Measuring latency for simple lookups versus complex aggregations.
  - Reliability: Simulating node failures to demonstrate the trade-off between Consistency and Availability.

2. System Architecture and Configuration

The system runs in a containerized environment using Docker to ensure reproducibility.

Software Configuration:
- Orchestration: Docker Compose
- Relational Database: PostgreSQL 16
- NoSQL Database: MongoDB 7.0
- Programming Language: Python 3.11
- Key Libraries: psycopg2, pymongo, matplotlib, faker

Hardware Configuration:
- Execution Environment: Local Machine (MacBook Air M2)
- Resource Allocation: Standard Docker container limits.

3. Data Model

The dataset represents an E-commerce platform containing 100 users and 500 products.

Strategy 1: Relational (PostgreSQL)
The data is normalized into three tables: users, products, and orders. Relationships are established via Foreign Keys (user_id). Retrieving full order details requires JOIN operations.

Strategy 2: Document-Oriented (MongoDB)
The data is denormalized using the Embedded Document pattern. The orders collection contains the full product details nested within the items array. This optimizes read performance by eliminating joins.

<img width="3026" height="1598" alt="image" src="https://github.com/user-attachments/assets/7d58d285-f6cd-446f-ac7a-c6fcb441e29f" />


4. Relevant Code Snippets

A. Data Generation
A custom generator creates semantically consistent data for both databases simultaneously.

File: src/generate_data.py
def generate_smart_product():
    category = random.choice(list(PRODUCT_TEMPLATES.keys()))
    template = PRODUCT_TEMPLATES[category]
    noun = random.choice(template["nouns"])
    name = f"{adj} {noun} {fake.year()}"
    return {"name": name, "category": category, "price": price}

B. Benchmark Logic
Comparison of aggregation complexity.

PostgreSQL Query (SQL Join):
SELECT u.city, SUM(o.total_amount) 
FROM users u 
JOIN orders o ON u.id = o.user_id 
GROUP BY u.city 
ORDER BY SUM(o.total_amount) DESC LIMIT 5;

MongoDB Query (Aggregation Pipeline):
pipeline = [
    {"$group": {"_id": "$user_city_snapshot", "total": {"$sum": "$total_amount"}}},
    {"$sort": {"total": -1}},
    {"$limit": 5}
]

5. Experimental Results and Interpretation
<img width="1000" height="600" alt="benchmark_results" src="https://github.com/user-attachments/assets/4cbaa307-92e1-4f0a-aad1-c62b785f5459" />

The following chart presents the average latency recorded during the benchmark.
Simple Query: Both systems perform equally well for primary key lookups using indexes.
Aggregate Query: MongoDB performs faster for this specific query because data is pre-joined (embedded), whereas SQL must calculate joins at runtime.
Reliability (Chaos Test): When the node stops, PostgreSQL refuses connections immediately (Consistency). MongoDB client handles the timeout and recovers automatically (Availability/Partition Tolerance).

6. Screenshots proving code functionality
  - docker containers
   <img width="3420" height="2214" alt="image" src="https://github.com/user-attachments/assets/24167997-5947-4348-a804-08c7f5602255" />
  - generate_data.py
   <img width="3420" height="2214" alt="image" src="https://github.com/user-attachments/assets/88d67d4b-9c26-45c3-8038-554cd2fe287c" />
  - sql_ops.py
    <img width="3420" height="2214" alt="image" src="https://github.com/user-attachments/assets/d8142cd4-36df-470e-bea5-a4a3e78648c8" />
  - mongo_ops.py
    <img width="3420" height="2214" alt="image" src="https://github.com/user-attachments/assets/e8c3767c-7b07-4d3c-a2a7-cf1f3213b746" />
  - benchmark_full.py
    <img width="3420" height="2214" alt="image" src="https://github.com/user-attachments/assets/a6d9ed47-76d7-4419-a10c-a5f817fea0d7" />
  - chaos_test.py
    <img width="3420" height="2214" alt="image" src="https://github.com/user-attachments/assets/58d65659-e32a-4eca-bc3c-ce06d38423a1" />

7. Video demonstration
   https://youtu.be/sQ_jJ6FF424

Bibliography

1. PostgreSQL Documentation. Available at: https://www.postgresql.org/docs/
2. MongoDB Manual. Available at: https://www.mongodb.com/docs/manual/
3. Brewer, E. A. (2012). CAP twelve years later: How the "rules" have changed.
4. Python Faker Documentation. Available at: https://faker.readthedocs.io/
5. Google, Gemini, https://gemini.google.com/, Date generated: January 22nd, 2026.

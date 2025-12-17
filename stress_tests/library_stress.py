import asyncio
import httpx
import time
import random
import psycopg2

import os

# Configuration
BASE_URL = "http://localhost:8000"
CONCURRENT_REQUESTS = 50 
TOTAL_RECORDS = 1000 

# Database config 
DB_NAME = os.getenv("DB_NAME", "odoo_fastapi")
DB_USER = os.getenv("DB_USER", "odoo")
DB_PASSWORD = os.getenv("DB_PASSWORD", "odoo")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_admin_api_key():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT api_key FROM res_users WHERE login='admin'")
        res = cur.fetchone()
        conn.close()
        if res:
            return res[0]
        return None
    except Exception as e:
        print(f"Error fetching API Key: {e}")
        return None

async def create_book(client, headers, idx):
    data = {
        "name": f"Stress Book {idx}",
        "isbn": f"STRESS-{idx}",
        "pages": random.randint(100, 1000),
        "rating": random.randint(1, 5) # Test inheritance field too
    }
    response = await client.post(f"{BASE_URL}/library/books", json=data, headers=headers)
    return response

async def update_book(client, headers, book_id, idx):
    data = {
        "name": f"Updated Stress Book {idx}",
        "pages": 999
    }
    response = await client.put(f"{BASE_URL}/library/books/{book_id}", json=data, headers=headers)
    return response

async def delete_book(client, headers, book_id):
    response = await client.delete(f"{BASE_URL}/library/books/{book_id}", headers=headers)
    return response

async def main():
    print("--- Starting Stress Test ---")
    
    # 1. Get API Key
    api_key = get_admin_api_key()
    if not api_key:
        print("Could not retrieve Admin API Key. Please ensure DB is running and admin exists.")
        return
        
    print(f"Using API Key: {api_key}")
    headers = {"x-api-key": api_key}
    
    # 2. Setup HTTPX Client
    limits = httpx.Limits(max_keepalive_connections=CONCURRENT_REQUESTS, max_connections=CONCURRENT_REQUESTS)
    async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
        
        # PHASE 1: CREATE
        print(f"\n[PHASE 1] Creating {TOTAL_RECORDS} records...")
        start_time = time.time()
        created_ids = []
        
        # Process in batches to avoid overwhelming local OS file descriptors if TOTAL_RECORDS is huge
        # But for 1000 with 50 concurrency it's fine to just spawn tasks.
        # Let's chunk it.
        
        tasks = []
        for i in range(TOTAL_RECORDS):
            tasks.append(create_book(client, headers, i))
            
        results = await asyncio.gather(*tasks)
        
        success_count = 0
        for r in results:
            if r.status_code == 200:
                created_ids.append(r.json()['id'])
                success_count += 1
            else:
                print(f"Failed to create: {r.status_code} - {r.text}")
                
        duration = time.time() - start_time
        print(f"Created {success_count} records in {duration:.2f} seconds ({success_count/duration:.2f} req/s)")
        
        # PHASE 2: UPDATE
        if not created_ids:
            print("No records created. Aborting.")
            return

        print(f"\n[PHASE 2] Updating {len(created_ids)} records...")
        start_time = time.time()
        tasks = []
        for i, book_id in enumerate(created_ids):
            tasks.append(update_book(client, headers, book_id, i))
            
        results = await asyncio.gather(*tasks)
        
        success_count = 0
        for r in results:
            if r.status_code == 200:
                success_count += 1
            else:
                print(f"Failed to update {book_id}: {r.status_code}")

        duration = time.time() - start_time
        print(f"Updated {success_count} records in {duration:.2f} seconds ({success_count/duration:.2f} req/s)")

        # PHASE 3: DELETE
        print(f"\n[PHASE 3] Deleting {len(created_ids)} records...")
        start_time = time.time()
        tasks = []
        for book_id in created_ids:
            tasks.append(delete_book(client, headers, book_id))
            
        results = await asyncio.gather(*tasks)
        
        success_count = 0
        for r in results:
            if r.status_code == 200:
                success_count += 1
            else:
                 print(f"Failed to delete {book_id}: {r.status_code}")

        duration = time.time() - start_time
        print(f"Deleted {success_count} records in {duration:.2f} seconds ({success_count/duration:.2f} req/s)")
        
    print("\n--- Stress Test Completed ---")

if __name__ == "__main__":
    asyncio.run(main())

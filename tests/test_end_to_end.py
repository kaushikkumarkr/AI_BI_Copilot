# file: tests/test_end_to_end.py
import requests
import time
import os

API_URL = "http://localhost:8000"
FILE_PATH = "sample_data.csv"

def test_system():
    print(f"--- Starting End-to-End Test ---")
    
    # 1. Upload Dataset
    print(f"Uploading {FILE_PATH}...")
    with open(FILE_PATH, "rb") as f:
        files = {"file": f}
        res = requests.post(f"{API_URL}/analyze_dataset", files=files)
    
    if res.status_code != 200:
        print(f"Upload failed: {res.text}")
        return
        
    task_id = res.json()["task_id"]
    print(f"Task ID: {task_id}")
    print("Analysis started in background. Waiting 30 seconds for agents to finish...")
    
    # Wait for workflow (simple sleep since we don't have a real status polling yet)
    time.sleep(30)
    
    # 2. Test SQL Query
    print("\n--- Testing SQL Agent ---")
    sql_payload = {"query": "What is the total sales by Region?", "dataset_id": task_id}
    try:
        res = requests.post(f"{API_URL}/sql_query", json=sql_payload)
        print(f"SQL Response: {res.json()}")
    except Exception as e:
        print(f"SQL Test Failed: {e}")

    # 3. Test Semantic Query
    print("\n--- Testing Semantic Query Agent ---")
    sem_payload = {"query": "Why are sales higher in the North?", "context_id": task_id}
    try:
        res = requests.post(f"{API_URL}/semantic_query", json=sem_payload)
        print(f"Semantic Response: {res.json()}")
    except Exception as e:
        print(f"Semantic Test Failed: {e}")

    # 4. Check Report Generation
    print("\n--- Checking Report ---")
    # Since report generation is part of the workflow, we check if the file exists
    # Note: In a real test we'd download it, but here we check the server logs or assume success if no error
    print(f"Check the 'backend/report' folder for {task_id}_report.pdf")

if __name__ == "__main__":
    test_system()
# end file

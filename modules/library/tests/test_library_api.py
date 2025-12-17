import requests
import pytest

# Integration Tests requiring running container
# Run with: pytest tests/test_library_api.py

BASE_URL = "http://localhost:8000"
API_KEY = "mysecretkey"
HEADERS = {"x-api-key": API_KEY}

def test_api_access_control():
    # Test unauthorized
    resp = requests.get(f"{BASE_URL}/library/books", headers={"x-api-key": "bad"})
    assert resp.status_code == 401

    # Test authorized
    resp = requests.get(f"{BASE_URL}/library/books", headers=HEADERS)
    assert resp.status_code == 200

def test_crud_flow():
    # 1. Create
    payload = {
        "name": "Integration Test Book",
        "isbn": "123-456",
        "pages": 100
    }
    resp = requests.post(f"{BASE_URL}/library/books", json=payload, headers=HEADERS)
    assert resp.status_code == 200, f"Error: {resp.text}"
    data = resp.json()
    assert "id" in data
    book_id = data["id"]
    assert data["name"] == payload["name"]
    print(f"Created Book ID: {book_id}")

    # 2. Read
    resp = requests.get(f"{BASE_URL}/library/books", headers=HEADERS)
    assert resp.status_code == 200
    books = resp.json()
    assert any(b["id"] == book_id for b in books)

    # 3. Update
    update_payload = {"name": "Updated Title", "pages": 150}
    resp = requests.put(f"{BASE_URL}/library/books/{book_id}", json=update_payload, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["success"] == True

    # Verify Update in DB via Read
    resp = requests.get(f"{BASE_URL}/library/books", headers=HEADERS)
    books = resp.json()
    updated_book = next(b for b in books if b["id"] == book_id)
    assert updated_book["name"] == "Updated Title"
    assert updated_book["pages"] == 150

    # 4. Delete
    resp = requests.delete(f"{BASE_URL}/library/books/{book_id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["success"] == True

    # Verify Delete
    resp = requests.get(f"{BASE_URL}/library/books", headers=HEADERS)
    books = resp.json()
    assert not any(b["id"] == book_id for b in books)

def test_create_validation():
    # Missing required field 'name'
    payload = {"isbn": "000"}
    resp = requests.post(f"{BASE_URL}/library/books", json=payload, headers=HEADERS)
    assert resp.status_code == 422 # FastAPI validation error

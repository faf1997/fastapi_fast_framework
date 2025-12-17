import requests
import pytest

BASE_URL = "http://web:8000"
HEADERS = {"x-api-key": "admin"} # Using admin key hardcoded or retrieved? 
# Wait, the admin key is random uuid. We need to get it or set a static one for tests.
# OR we can assume the one logged. But for automation, better to use the user created in previous tests or fetch from DB.
# In test_library_api.py we used a user 'api' with key 'mysecretkey' created via SQL.
# Let's reuse that user/key.

HEADERS = {"x-api-key": "mysecretkey"}

def test_extension_field():
    # 1. Create a book with the new 'rating' field
    payload = {
        "name": "Extended Book",
        "isbn": "999-999",
        "pages": 50,
        "rating": 5
    }
    resp = requests.post(f"{BASE_URL}/library/books", json=payload, headers=HEADERS)
    assert resp.status_code == 200, f"Error: {resp.text}"
    data = resp.json()
    book_id = data["id"]
    
    # 2. Read the book back and check rating
    # Note: Our default GET /library/books might not return all fields if read() isn't dynamic enough 
    # OR if the controller output model limits it.
    # The controller returns `book.read()` which returns all fields in `_fields`.
    # Since we monkey patched `_fields`, it should appear.
    
    resp = requests.get(f"{BASE_URL}/library/books", headers=HEADERS)
    assert resp.status_code == 200
    books = resp.json()
    
    # Find our book
    my_book = next((b for b in books if b["id"] == book_id), None)
    assert my_book is not None
    assert "rating" in my_book, f"Rating field missing in response: {my_book}"
    assert my_book["rating"] == 5

    # 3. Update rating
    update_payload = {"rating": 3}
    resp = requests.put(f"{BASE_URL}/library/books/{book_id}", json=update_payload, headers=HEADERS)
    assert resp.status_code == 200
    
    # Verify update
    resp = requests.get(f"{BASE_URL}/library/books", headers=HEADERS)
    books = resp.json()
    my_book = next((b for b in books if b["id"] == book_id), None)
    assert my_book["rating"] == 3

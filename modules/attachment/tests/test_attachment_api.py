import pytest
import io
from fastapi.testclient import TestClient
from main import app
from core.database import Database
from core.orm.registry import Registry
from core.module_loader import ModuleLoader
from core.orm.environment import Environment
from core.tools.config import config

class TestAttachmentAPI:
    # We don't use class-level client because we need lifespan event trigger.
    # But if we use it per test, we might re-init DB pool/modules repeatedly which is okay for tests.
    
    def test_upload_attachment(self):
        with TestClient(app) as client:
            file_content = b"Integration Test Content"
            files = {
                "file": ("test_api.txt", io.BytesIO(file_content), "text/plain")
            }
            data = {
                "res_model": "res.partner",
                "res_id": 1
            }
            
            response = client.post("/attachment/upload", files=files, data=data)
            assert response.status_code == 200
            json_resp = response.json()
            assert "id" in json_resp
            return json_resp["id"]

    def test_download_attachment(self):
        with TestClient(app) as client:
            # We need to reuse the same DB state. 
            # TestClient lifespan will init DB and modules.
            # But "upload" test logic needs to be repeated or we assume persistence.
            # Since tests run sequentially and DB persists (docker), it should be fine IF we separate create.
            
            # Helper to create
            file_content = b"Download Content"
            files = {"file": ("dl.txt", io.BytesIO(file_content), "text/plain")}
            resp = client.post("/attachment/upload", files=files)
            att_id = resp.json()["id"]
            
            response = client.get(f"/attachment/{att_id}/download")
            assert response.status_code == 200
            assert response.content == file_content
            assert "filename=dl.txt" in response.headers["content-disposition"]

    def test_update_attachment(self):
        with TestClient(app) as client:
            file_content = b"Original"
            files = {"file": ("orig.txt", io.BytesIO(file_content), "text/plain")}
            resp = client.post("/attachment/upload", files=files)
            att_id = resp.json()["id"]
            
            # Update name
            response = client.put(f"/attachment/{att_id}", data={"name": "updated_api.txt"})
            assert response.status_code == 200
            
            resp_dl = client.get(f"/attachment/{att_id}/download")
            assert "filename=updated_api.txt" in resp_dl.headers["content-disposition"]
            
            # Update content
            new_content = b"Updated Content API"
            files = {"file": ("updated_api.txt", io.BytesIO(new_content), "text/plain")}
            client.put(f"/attachment/{att_id}", files=files)
            
            resp_dl2 = client.get(f"/attachment/{att_id}/download")
            assert resp_dl2.content == new_content

    def test_delete_attachment(self):
        with TestClient(app) as client:
            files = {"file": ("del.txt", io.BytesIO(b"del"), "text/plain")}
            resp = client.post("/attachment/upload", files=files)
            att_id = resp.json()["id"]
            
            response = client.delete(f"/attachment/{att_id}")
            assert response.status_code == 200
            
            resp_dl = client.get(f"/attachment/{att_id}/download")
            assert resp_dl.status_code == 404

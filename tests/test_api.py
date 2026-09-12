import io
import json
import warnings
import zipfile

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

# Suppress TestClient import warning in older Starlette versions used by FastAPI 0.111.0
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from api.routes import app

client = TestClient(app)

def create_dummy_image(size=(256, 256), color=(255, 0, 0)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_dummy_jpeg(size=(512, 512)):
    arr = np.random.randint(0, 255, (size[0], size[1], 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cryptonite"}

class TestCapacity:
    def test_capacity_png(self):
        png_bytes = create_dummy_image()
        response = client.post(
            "/capacity",
            files={"file": ("test.png", png_bytes, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["carrier_type"] == "PngCarrier"
        assert data["capacity_bytes"] > 0

    def test_capacity_unsupported(self):
        response = client.post(
            "/capacity",
            files={"file": ("test.txt", b"hello", "text/plain")}
        )
        assert response.status_code == 400
        assert "Unsupported carrier format" in response.json()["detail"]

class TestEmbedExtract:
    def test_embed_extract_png(self):
        png_bytes = create_dummy_image()
        payload = b"Secret payload data"
        passphrase = "test_passphrase"

        # 1. Embed
        response = client.post(
            "/embed",
            files={
                "carrier": ("cover.png", png_bytes, "image/png"),
                "payload": ("secret.txt", payload, "text/plain")
            },
            data={"passphrase": passphrase}
        )
        assert response.status_code == 200
        assert "x-embed-metadata" in response.headers
        stego_bytes = response.content

        # 2. Extract
        response2 = client.post(
            "/extract",
            files={"stego": ("stego.png", stego_bytes, "image/png")},
            data={"passphrase": passphrase}
        )
        assert response2.status_code == 200
        assert response2.content == payload
        assert "x-extract-metadata" in response2.headers

    def test_embed_capacity_exceeded(self):
        png_bytes = create_dummy_image(size=(16, 16)) # Very small capacity
        payload = b"A" * 10000 # Large payload
        response = client.post(
            "/embed",
            files={
                "carrier": ("cover.png", png_bytes, "image/png"),
                "payload": ("secret.txt", payload, "text/plain")
            },
            data={"passphrase": "test"}
        )
        assert response.status_code == 413
        assert "exceeds capacity" in response.json()["detail"]

    def test_extract_wrong_passphrase(self):
        png_bytes = create_dummy_image()
        payload = b"Secret payload data"

        response = client.post(
            "/embed",
            files={
                "carrier": ("cover.png", png_bytes, "image/png"),
                "payload": ("secret.txt", payload, "text/plain")
            },
            data={"passphrase": "correct"}
        )
        stego_bytes = response.content

        response2 = client.post(
            "/extract",
            files={"stego": ("stego.png", stego_bytes, "image/png")},
            data={"passphrase": "wrong"}
        )
        assert response2.status_code == 400
        assert "invalid passphrase" in response2.json()["detail"] or "MAC check failed" in response2.json()["detail"]

class TestAnalyze:
    def test_analyze_identical(self):
        img_bytes = create_dummy_image()
        response = client.post(
            "/analyze",
            files={
                "cover": ("cover.png", img_bytes, "image/png"),
                "stego": ("stego.png", img_bytes, "image/png")
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ssim_score"] == 1.0
        assert data["verdict"] == "SAFE"

    def test_analyze_mismatch(self):
        img1 = create_dummy_image(size=(32, 32))
        img2 = create_dummy_image(size=(64, 64))
        response = client.post(
            "/analyze",
            files={
                "cover": ("cover.png", img1, "image/png"),
                "stego": ("stego.png", img2, "image/png")
            }
        )
        assert response.status_code == 400
        assert "dimension mismatch" in response.json()["detail"]

class TestBatch:
    def test_batch_embed(self):
        png_bytes = create_dummy_image()
        jpg_bytes = create_dummy_jpeg()

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("img1.png", png_bytes)
            zf.writestr("img2.jpg", jpg_bytes)
            zf.writestr("unsupported.txt", b"hello")

        zip_buf.seek(0)

        response = client.post(
            "/batch/embed",
            files={
                "archive": ("batch.zip", zip_buf, "application/zip"),
                "payload": ("secret.txt", b"secret", "text/plain")
            },
            data={"passphrase": "test"}
        )

        assert response.status_code == 200

        meta = json.loads(response.headers["x-batch-metadata"])
        assert meta["total"] == 3
        assert meta["succeeded"] == 2
        assert meta["failed"] == 1
        assert "unsupported.txt (unsupported)" in meta["failed_files"][0]

        out_zip = zipfile.ZipFile(io.BytesIO(response.content))
        assert "stego_img1.png" in out_zip.namelist()
        assert "stego_img2.jpg" in out_zip.namelist()

class TestErrorCodes:
    def test_validation_error_422(self):
        response = client.post("/embed") # Missing all fields
        assert response.status_code == 422
        
    def test_embed_unsupported_carrier(self):
        response = client.post(
            "/embed",
            files={
                "carrier": ("cover.txt", b"not an image", "text/plain"),
                "payload": ("secret.txt", b"payload", "text/plain")
            },
            data={"passphrase": "test"}
        )
        assert response.status_code == 400
        assert "Unsupported carrier format" in response.json()["detail"]
        
    def test_extract_unsupported_carrier(self):
        response = client.post(
            "/extract",
            files={"stego": ("stego.txt", b"not an image", "text/plain")},
            data={"passphrase": "test"}
        )
        assert response.status_code == 400
        assert "Unsupported carrier format" in response.json()["detail"]
        
    def test_analyze_unsupported_carrier(self):
        img_bytes = create_dummy_image()
        response = client.post(
            "/analyze",
            files={
                "cover": ("cover.txt", b"not an image", "text/plain"),
                "stego": ("stego.png", img_bytes, "image/png")
            }
        )
        assert response.status_code == 400
        assert "Invalid image format" in response.json()["detail"]

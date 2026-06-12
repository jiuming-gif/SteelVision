import io
from unittest.mock import AsyncMock, patch

from PIL import Image


def test_register_new_user(client):
    resp = client.post("/register", json={"username": "testuser", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert "id" in data


def test_register_duplicate(client):
    client.post("/register", json={"username": "dupuser", "password": "secret123"})
    resp = client.post("/register", json={"username": "dupuser", "password": "secret123"})
    assert resp.status_code == 400
    assert "用户名已存在" in resp.json()["detail"]


def test_login_success(client):
    client.post("/register", json={"username": "loginuser", "password": "pass123"})
    resp = client.post("/login", data={"username": "loginuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "欢迎回来" in resp.json()["message"]


def test_login_wrong_password(client):
    client.post("/register", json={"username": "wpuser", "password": "correct"})
    resp = client.post("/login", data={"username": "wpuser", "password": "wrong"})
    assert resp.status_code == 400
    assert "密码错误" in resp.json()["detail"]


def test_login_user_not_found(client):
    resp = client.post("/login", data={"username": "nobody", "password": "nope"})
    assert resp.status_code == 400
    assert "用户不存在" in resp.json()["detail"]


def test_predict_with_image(client):
    img = Image.new("RGB", (64, 64), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    mock_detect = AsyncMock(return_value=([[0, 1, 0], [0, 0, 1]], 42.0))
    with patch("main.perform_detection", mock_detect):
        resp = client.post("/predict", files={"file": ("test.jpg", buf, "image/jpeg")})

    assert resp.status_code == 200
    data = resp.json()
    assert "mask" in data
    assert "model_time_ms" in data
    assert "detection_result" in data
    assert "advice_type" in data
    assert "advice_content" in data


def test_predict_without_file(client):
    resp = client.post("/predict")
    assert resp.status_code == 422


def test_chat_reply(client):
    resp = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert resp.status_code == 200
    reply = resp.json()["reply"]
    assert len(reply) > 0


def test_get_empty_feed(client):
    resp = client.get("/api/community/feed")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_post(client):
    reg_resp = client.post("/register", json={"username": "poster", "password": "pass"})
    user_id = reg_resp.json()["id"]

    post_resp = client.post("/api/community/post", data={
        "title": "Test Post",
        "content": "This is a test.",
        "author_id": str(user_id),
    })
    assert post_resp.status_code == 200
    assert post_resp.json()["title"] == "Test Post"

    feed_resp = client.get("/api/community/feed")
    assert feed_resp.status_code == 200
    assert len(feed_resp.json()) == 1


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Welcome" in resp.json()["message"]

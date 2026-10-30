from fastapi.testclient import TestClient
from app.main import app


def test_health_and_chat():
    with TestClient(app) as c:
        h = c.get("/api/health").json()
        assert h["chunks"] > 10

        r = c.post("/api/chat", json={"message": "How do I get a refund?", "session_id": "t1"}).json()
        assert not r["escalate"]
        assert any("billing" in s["source"] for s in r["sources"])
        assert "refund" in r["answer"].lower()

        r = c.post("/api/chat", json={"message": "what are the API rate limits for pro?", "session_id": "t2"}).json()
        assert "600" in r["answer"]


def test_escalation_and_ticket():
    with TestClient(app) as c:
        r = c.post("/api/chat", json={"message": "quantum banana helicopter recipe", "session_id": "t3"}).json()
        assert r["escalate"]
        r = c.post("/api/chat", json={"message": "I want to talk to a human", "session_id": "t3"}).json()
        assert r["escalate"]
        t = c.post("/api/tickets", json={"session_id": "t3", "email": "a@b.com"}).json()
        assert t["ticket_id"] >= 1
        assert c.post("/api/tickets", json={"email": "bad"}).status_code == 400
        assert len(c.get("/api/tickets").json()) >= 1


def test_websocket_streaming_and_upload():
    with TestClient(app) as c:
        files = {"file": ("shipping.md", b"# Warranty\n\nAcme hardware keys carry a two year warranty against defects.", "text/markdown")}
        assert c.post("/api/upload", files=files).status_code == 200
        with c.websocket_connect("/ws/chat") as ws:
            ws.send_json({"message": "how long is the warranty on hardware keys?", "session_id": "w1"})
            types, text = [], ""
            while True:
                ev = ws.receive_json()
                types.append(ev["type"])
                text += ev.get("text", "")
                if ev["type"] == "done":
                    break
        assert "sources" in types and types.count("token") > 3
        assert "two year" in text.lower()
        assert c.post("/api/upload", files={"file": ("x.exe", b"a")}).status_code == 400

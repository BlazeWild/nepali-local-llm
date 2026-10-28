from fastapi.testclient import TestClient

from app import main


def test_stateless_generation(monkeypatch):
    async def fake_generate(messages, temperature, top_p, top_k, max_tokens):
        return "उत्तर: " + messages[-1]["content"]

    monkeypatch.setattr(main, "generate", fake_generate)
    with TestClient(main.app) as client:
        response = client.post(
            "/v1/generate",
            json={"messages": [{"role": "user", "content": "नमस्ते"}]},
        )
        assert response.status_code == 200
        assert response.json() == {"response": "उत्तर: नमस्ते", "queue_position": 1}

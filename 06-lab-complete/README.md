# Lab 12 — Complete Production Agent

Kết hợp TẤT CẢ những gì đã học trong 1 project hoàn chỉnh.

## Checklist Deliverable

- [x] Dockerfile (multi-stage, < 500 MB)
- [x] docker-compose.yml (nginx + agent + redis)
- [x] .dockerignore
- [x] Health check endpoint (`GET /health`)
- [x] Readiness endpoint (`GET /ready`)
- [x] API Key authentication
- [x] Rate limiting
- [x] Cost guard
- [x] Config từ environment variables
- [x] Structured logging
- [x] Graceful shutdown
- [x] Public URL ready (Render config)

---

## Cấu Trúc

```
06-lab-complete/
├── app/
│   ├── main.py         # Entry point — kết hợp tất cả
│   ├── config.py       # 12-factor config
│   ├── auth.py         # API Key authentication
│   ├── rate_limiter.py # Redis-backed rate limiting
│   ├── cost_guard.py   # Redis-backed budget protection
│   └── mock_llm.py     # Offline mock LLM
├── Dockerfile          # Multi-stage, production-ready
├── docker-compose.yml  # Full stack: nginx + agent + redis
├── nginx.conf          # Local load balancer
├── render.yaml         # Deploy Render (selected platform)
├── railway.toml        # Railway reference only
├── .env.example        # Template
├── .dockerignore
└── requirements.txt
```

---

## Chạy Local

```bash
# 1. Setup
cp .env.example .env

# 2. Chạy với Docker Compose
docker compose up

# 3. Test
curl http://localhost/health

# 4. Lấy API key từ .env, test endpoint
API_KEY=$(grep AGENT_API_KEY .env 2>/dev/null | cut -d= -f2)
[ -z "$API_KEY" ] && API_KEY=$(grep AGENT_API_KEY .env.example | cut -d= -f2)
curl -H "X-API-Key: $API_KEY" \
     -X POST http://localhost/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What is deployment?", "session_id": "demo"}'
```

---

## Deploy Render

1. Push repo lên GitHub
2. Render Dashboard → New → Blueprint
3. Connect repo → Render đọc `render.yaml`
4. Blueprint tạo web service và Render Key Value (`ai-agent-redis`)
5. Set secret `OPENAI_API_KEY` nếu muốn dùng LLM thật; `AGENT_API_KEY` và `JWT_SECRET` được generate tự động
6. Deploy → Nhận URL!

---

## Kiểm Tra Production Readiness

```bash
python check_production_ready.py
```

Script này kiểm tra tất cả items trong checklist và báo cáo những gì còn thiếu.

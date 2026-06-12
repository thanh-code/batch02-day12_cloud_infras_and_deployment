# Section 5 - Scaling & Reliability

## Develop: Health And Graceful Shutdown

```
develop/
├── app.py
├── requirements.txt
└── utils/mock_llm.py
```

Run:

```bash
cd develop
pip install -r requirements.txt
python app.py
```

Test:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl -X POST "http://localhost:8000/ask?question=Hello"
```

## Production: Stateless Scaling

```
production/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
├── test_stateless.py
└── utils/mock_llm.py
```

Run the load-balanced stack:

```bash
cd production
docker compose up --build --scale agent=3
```

In another terminal:

```bash
curl http://localhost:8080/health
python test_stateless.py
```

Stop:

```bash
docker compose down
```

The demo stores session history in Redis, so any scaled agent instance can continue the same conversation.

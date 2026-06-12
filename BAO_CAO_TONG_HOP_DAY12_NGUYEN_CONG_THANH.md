# Báo Cáo Tổng Hợp Day 12 - Cloud Infrastructure And Deployment

> Sinh viên: Nguyễn Công Thành - 2A202600696  
> Ngay bao cao: 12/06/2026  
> Nen tang cloud uu tien: Render

## 1. Muc Tieu Bao Cao

File nay tong hop phan cau hoi - tra loi va bao cao ket qua hoan thien lab Day 12. Noi dung duoc viet dua tren cac file huong dan trong repo:

- `CODE_LAB.md`: de bai chinh tu Part 1 den Part 6.
- `DAY12_DELIVERY_CHECKLIST.md`: yeu cau nop bai, mission answers, source code, deployment information.
- `README.md`, `QUICK_START.md`, `LEARNING_PATH.md`: huong dan tong quan.
- Cac thu muc `01-localhost-vs-production` den `06-lab-complete`: code mau, code production, Docker, cloud deployment, API security, scaling va final project.

Muc tieu hoc tap cua lab:

- Hieu su khac nhau giua localhost/development va production.
- Dong goi ung dung AI agent bang Docker.
- Chay stack bang Docker Compose.
- Deploy len cloud, trong bai nay uu tien Render.
- Bao mat API bang API key/JWT, rate limiting va cost guard.
- Thiet ke ung dung co kha nang scale: stateless, health check, readiness check, graceful shutdown, load balancing.
- Hoan thien final production-ready AI agent trong `06-lab-complete`.

## 2. Tong Hop File Va Vai Tro

| File/thu muc | Vai tro | Trang thai |
|---|---|---|
| `CODE_LAB.md` | De bai, cac exercise, checkpoint | Dung lam tai lieu tham chieu, khong can sua |
| `DAY12_DELIVERY_CHECKLIST.md` | Checklist nop bai va rubric | Da doc de lap cau truc bao cao |
| `RUN_01_TO_05_RENDER_PLAN.md` | Ke hoach va ket qua chay Part 01-05, uu tien Render | Da co ke hoach rieng |
| `TONG_QUAN_KIEN_THUC_DAY12.md` | Tai lieu tong hop kien thuc co ban/nang cao | Da bo sung |
| `HUONG_DAN_RENDER_CHO_NGUOI_MOI.md` | Huong dan hoc va su dung Render cho nguoi moi | Da bo sung |
| `01-localhost-vs-production/` | So sanh develop va production app | Da cap nhat README theo folder that |
| `02-docker/` | Docker single-stage, multi-stage, Docker Compose | Da bo sung production requirements va compose |
| `03-cloud-deployment/render/` | Render Blueprint demo | Da bo sung app, requirements, render.yaml |
| `04-api-gateway/` | API security: API key, JWT, rate limit, cost guard | Da doc va tong hop cau tra loi |
| `05-scaling-reliability/` | Health/readiness, stateless, load balancing | Da bo sung README va production Dockerfile |
| `06-lab-complete/` | Final production-ready AI agent | Da hoan thien va check 20/20 |

## 3. Part 1 - Localhost Vs Production

### Exercise 1.1 - Cac anti-pattern trong ban develop

Nhung van de thuong gap trong app chay local nhung chua san sang production:

1. Hardcode secret/API key trong source code.
2. Hardcode port, host hoac cau hinh truc tiep trong file Python.
3. Bat debug mode khi chay production.
4. Thieu endpoint `/health` de platform biet app con song hay khong.
5. Thieu endpoint `/ready` de biet app da san sang nhan traffic hay chua.
6. Dung `print()` thay cho structured logging.
7. Khong xu ly shutdown, container bi tat dot ngot co the lam mat request dang xu ly.
8. Khong tach config khoi code nen kho deploy len nhieu moi truong.
9. Phu thuoc vao state trong memory, khi scale nhieu instance se bi mat/lech state.
10. Khong co co che bao ve chi phi neu thay mock LLM bang LLM that.

### Exercise 1.3 - Bang so sanh develop va production

| Feature | Develop | Production | Tai sao quan trong? |
|---|---|---|---|
| Config | Hardcode trong code | Lay tu environment variables | De deploy tren local/staging/production ma khong sua code |
| Secrets | Co nguy co nam trong source | Dung `.env` local va dashboard secrets tren cloud | Giam nguy co lo API key |
| Host/port | Co the co dinh | Doc `HOST`, `PORT` tu env | Cloud platform thuong gan port dong |
| Health check | Co the thieu | Co `/health` | Platform dung de restart container khi app hong |
| Readiness check | Co the thieu | Co `/ready` | Chi nhan traffic khi dependency san sang |
| Logging | `print()` | JSON structured logging | De loc log, debug va monitoring tot hon |
| Shutdown | Tat dot ngot | Graceful shutdown/SIGTERM | Giam mat request khi deploy/restart |
| State | Memory trong process | Redis hoac external storage | Scale nhieu instance khong mat conversation |
| Debug | De bat khi local | Tat trong production | Tranh ro ri thong tin noi bo |

### Checkpoint Part 1

- Da hieu vi sao hardcode secrets nguy hiem: secret co the bi commit len GitHub va bi dung trai phep.
- Da hieu environment variables: cau hinh nam ngoai source code.
- Da hieu health check: kiem tra process/app con song.
- Da hieu graceful shutdown: khi nhan SIGTERM, app ngung nhan request moi va co thoi gian xu ly request cu.

## 4. Part 2 - Docker Containerization

### Exercise 2.1 - Tra loi cau hoi Dockerfile co ban

1. Base image la gi?

   Trong `02-docker/develop/Dockerfile`, base image la:

   ```dockerfile
   FROM python:3.11
   ```

   Day la image Python day du, de hoc va debug nhung kich thuoc lon.

2. Working directory la gi?

   Working directory la:

   ```dockerfile
   WORKDIR /app
   ```

   Tat ca lenh tiep theo trong Dockerfile se chay trong `/app` neu khong chi dinh duong dan khac.

3. Tai sao `COPY requirements.txt` truoc?

   Docker build theo layer cache. Neu copy `requirements.txt` truoc va cai dependency truoc, Docker co the dung lai layer cai thu vien khi code app thay doi nhung requirements khong doi. Cach nay giup build nhanh hon.

4. `CMD` khac `ENTRYPOINT` nhu the nao?

   - `CMD`: lenh mac dinh khi container start, de override bang command khac khi `docker run`.
   - `ENTRYPOINT`: lenh chinh cua container, kho override hon, hay dung khi image duoc thiet ke nhu mot executable.
   - Trong lab, `CMD ["python", "app.py"]` la phu hop vi ung dung chi can lenh start mac dinh.

### Exercise 2.3 - Multi-stage build

Trong `02-docker/production/Dockerfile` co 2 stage:

| Stage | Viec lam | Ly do |
|---|---|---|
| `builder` | Dung `python:3.11-slim`, cai packages vao `/root/.local` | Tach phan build/cai dependencies |
| `runtime` | Dung `python:3.11-slim`, copy dependencies da cai va code can chay | Runtime nhe hon, it file thua hon |

Tai sao image production nho hon:

- Dung `python:3.11-slim` thay vi `python:3.11` full.
- Runtime stage khong giu lai cache build va nhung file khong can thiet.
- Chay non-root user `appuser`, phu hop production hon.
- Co `HEALTHCHECK` de Docker/platform kiem tra app.

Ket qua da ghi nhan:

- Image production Part 2 build thanh cong voi ten `day12-part2-production`.
- Kich thuoc image production khoang 68 MB.
- Image develop chua do lai trong phien nay; co the do bang:

```bash
docker images my-agent:develop
```

### Exercise 2.4 - Docker Compose stack

Part 2 production dung Docker Compose de chay nhieu service. Kien truc tong quat:

```text
Client
  |
  v
Nginx reverse proxy / load balancer
  |
  v
FastAPI agent container
```

Cac service communicate qua Docker network noi bo. Client goi `localhost`, Nginx nhan request roi forward ve service agent.

Lenh kiem tra cau hinh:

```bash
docker compose config
```

Ket qua kiem chung trong repo:

- `docker compose config` cua Part 2 production da pass.
- Docker image production Part 2 build duoc.
- Runtime import pass.

### Checkpoint Part 2

- Da hieu Dockerfile gom base image, working directory, copy file, install dependencies va command start.
- Da hieu multi-stage build giup image gon va sach hon.
- Da hieu Docker Compose de orchestration nhieu container.
- Da biet debug container bang `docker logs`, `docker exec`, `docker compose ps`.

## 5. Part 3 - Cloud Deployment, Uu Tien Render

### Ly do chon Render

Theo yeu cau cua bai lam nay, Render duoc uu tien thay vi Railway. Render phu hop vi:

- Co dashboard web de deploy truc quan.
- Ho tro Web Service, Docker service, Blueprint `render.yaml`.
- Co free plan de hoc/lab.
- Co health check path.
- Co env vars va secret generation trong dashboard/blueprint.
- Co log viewer tren web.

### Exercise 3.1 - Railway deployment

Railway duoc giu lai nhu phuong an tham khao/prototype. Trong bao cao nay khong uu tien Railway.

Neu chay Railway thi flow co ban:

```bash
railway login
railway init
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
railway up
railway domain
```

Trang thai: khong deploy Railway vi da chon Render theo yeu cau.

### Exercise 3.2 - Render deployment

File demo Render:

```text
03-cloud-deployment/render/
├── app.py
├── requirements.txt
└── render.yaml
```

File final Render:

```text
06-lab-complete/
├── Dockerfile
├── render.yaml
└── app/
```

Trong `03-cloud-deployment/render/render.yaml`:

- `type: web`: tao web service.
- `runtime: python`: Render cai Python dependencies va chay app.
- `region: singapore`: chon khu vuc gan Viet Nam.
- `plan: free`: phu hop hoc tap.
- `rootDir: 03-cloud-deployment/render`: Render build tu dung folder demo.
- `buildCommand: pip install -r requirements.txt`: cai dependency.
- `startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT`: start FastAPI app.
- `healthCheckPath: /health`: Render dung endpoint nay de kiem tra service.
- `AGENT_API_KEY generateValue`: Render tu sinh secret.

Trong `06-lab-complete/render.yaml`:

- `runtime: docker`: Render build theo Dockerfile final.
- Co web service `ai-agent-production`.
- Co Render Key Value service `ai-agent-redis`.
- Env vars quan trong: `ENVIRONMENT`, `LOG_LEVEL`, `AGENT_API_KEY`, `JWT_SECRET`, `RATE_LIMIT_PER_MINUTE`, `MONTHLY_BUDGET_USD`, `REDIS_HOST`, `REDIS_PORT`.

### So sanh `render.yaml` va `railway.toml`

| Tieu chi | Render `render.yaml` | Railway `railway.toml` |
|---|---|---|
| Muc dich | Blueprint khai bao service, env vars, region, health check | Config build/start cho Railway |
| Cach deploy | Connect GitHub, New Blueprint/Web Service | Railway CLI hoac dashboard |
| Env vars | Khai bao trong YAML hoac dashboard | Set bang CLI/dashboard |
| Health check | Co `healthCheckPath` | Phu thuoc config/service |
| Multi-service | Blueprint co the tao web + keyvalue Redis | Railway co services rieng |
| Uu tien trong bai | Duoc chon la nen tang chinh | Chi tham khao |

### Huong dan chay Render tren web

1. Day repo len GitHub.
2. Dang ky/dang nhap tai `https://render.com`.
3. Chon `New` -> `Blueprint`.
4. Connect GitHub repository.
5. Chon repo cua lab Day 12.
6. Render doc `render.yaml`.
7. Xac nhan service web va Key Value/Redis.
8. Kiem tra env vars:
   - `ENVIRONMENT=production`
   - `AGENT_API_KEY` duoc generate
   - `JWT_SECRET` duoc generate
   - `RATE_LIMIT_PER_MINUTE=10`
   - `MONTHLY_BUDGET_USD=10.0`
9. Bam deploy.
10. Sau khi build xong, lay public URL tu dashboard.
11. Test:

```bash
curl https://<your-render-url>/health

curl -X POST https://<your-render-url>/ask \
  -H "X-API-Key: <AGENT_API_KEY_TREN_RENDER>" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello Render","session_id":"demo"}'
```

Trang thai public URL:

- Trong phien local nay chua dang nhap Render va chua deploy public.
- Can bo sung URL that va screenshot dashboard sau khi deploy tren tai khoan Render cua sinh vien.

### Checkpoint Part 3

- Da co cau hinh Render demo trong `03-cloud-deployment/render`.
- Da co cau hinh Render final trong `06-lab-complete/render.yaml`.
- Da hieu cach set environment variables tren Render.
- Da hieu cach xem logs trong dashboard Render.

## 6. Part 4 - API Security

### Exercise 4.1 - API Key authentication

API key duoc check trong header, thong thuong la:

```http
X-API-Key: <secret>
```

Neu thieu key hoac sai key:

- API tra ve `401 Unauthorized` hoac `403 Forbidden` tuy cach implement.
- Request khong duoc xu ly tiep.

Rotate key:

1. Tao key moi tren Render dashboard hoac `.env`.
2. Deploy/restart service de app doc key moi.
3. Cap nhat client dung key moi.
4. Thu hoi key cu.

Trong final project `06-lab-complete/app/auth.py`, API key duoc lay tu env `AGENT_API_KEY`, khong hardcode vao source code.

### Exercise 4.2 - JWT authentication

Trong `04-api-gateway/production/auth.py`:

- User login bang username/password demo.
- Server tao JWT co `sub`, `role`, `iat`, `exp`.
- Client gui token bang:

```http
Authorization: Bearer <token>
```

Flow:

```text
Client login -> Server verify credentials -> Server ky JWT -> Client dung JWT goi API -> Server verify signature/expiry -> Xu ly request
```

Loi thuong gap:

- Khong co token: `401 Authentication required`.
- Token het han: `401 Token expired`.
- Token sai chu ky: `403 Invalid token`.

### Exercise 4.3 - Rate limiting

Trong `04-api-gateway/production/rate_limiter.py`:

- Algorithm: Sliding Window Counter.
- User thuong: 10 requests/phut.
- Admin: 100 requests/phut.
- Khi vuot limit, API tra ve `429 Too Many Requests`.

Trong final project `06-lab-complete/app/rate_limiter.py`:

- Dung Redis sorted set khi co Redis.
- Fallback memory khi development khong co Redis.
- Production yeu cau Redis de giu rate limit dung khi scale nhieu instance.

Admin bypass/uu tien:

- Co the gan role admin tu JWT/API key metadata.
- Dung limit rieng cao hon cho admin.
- Khong nen bypass hoan toan trong production vi van can bao ve chi phi.

### Exercise 4.4 - Cost guard

Muc tieu cost guard:

- Uoc tinh chi phi truoc khi goi LLM.
- Ghi nhan usage sau khi co response.
- Chan request neu vuot budget.

Trong final project:

- Budget mac dinh: 10 USD/thang/user.
- Key Redis theo thang: `budget:{user_id}:{YYYY-MM}`.
- TTL khoang 32 ngay de tu reset vong doi key.
- Neu vuot budget tra ve `402 Payment Required`.

Pseudo-flow:

```text
Nhan request
  -> uoc tinh input/output tokens
  -> check monthly budget
  -> goi mock LLM
  -> record usage vao Redis
  -> tra ve response + usage metadata
```

### Checkpoint Part 4

- Da hieu API key authentication.
- Da hieu JWT flow.
- Da hieu sliding window rate limiting.
- Da hieu cost guard de tranh vuot tien khi dung LLM that.

## 7. Part 5 - Scaling And Reliability

### Exercise 5.1 - Health va readiness

`/health`:

- Dung cho liveness probe.
- Tra ve app con song.
- Khong nen phu thuoc qua nhieu dependency nang.

`/ready`:

- Dung cho readiness probe.
- Kiem tra app da san sang nhan traffic chua.
- Co the check Redis/database.
- Neu dependency bat buoc loi thi tra ve `503`.

Trong final project:

- `/health` tra ve status, version, environment, uptime, request count, status Redis/mock LLM.
- `/ready` tra ve ready khi app da startup xong va Redis san sang trong production.

### Exercise 5.2 - Graceful shutdown

Khi container/orchestrator muon tat app, no gui `SIGTERM`.

App production can:

1. Danh dau khong san sang nhan traffic moi.
2. Tra `/ready` ve 503 de load balancer rut traffic.
3. Cho request dang xu ly ket thuc trong grace period.
4. Dong ket noi Redis/database neu can.
5. Thoat process.

Trong `06-lab-complete/app/main.py`, signal handler dat:

- `_shutdown_requested = True`
- `_is_ready = False`

Sau do middleware chan request moi bang `503 Server is shutting down`.

### Exercise 5.3 - Stateless design

Anti-pattern:

```python
conversation_history = {}
```

Van de:

- Moi container co memory rieng.
- Khi scale 3 instances, request sau co the vao instance khac va mat history.
- Khi restart container, memory mat.

Production design:

- Luu history vao Redis.
- Key theo user/session.
- Gioi han so message va TTL.
- App instance nao xu ly cung doc duoc chung state.

Trong final project:

- `load_history`, `append_history`, `delete_history` dung Redis neu co.
- Development co fallback memory de de test local.
- Production yeu cau Redis.

### Exercise 5.4 - Load balancing

Kien truc:

```text
Client
  |
  v
Nginx
  |
  +--> Agent instance 1
  +--> Agent instance 2
  +--> Agent instance 3
        |
        v
      Redis
```

Lenh chay local:

```bash
docker compose up --scale agent=3
```

Y nghia:

- Nginx phan phoi request den nhieu instance.
- Neu mot instance chet, traffic van co the sang instance khac.
- Redis giu state chung nen conversation khong bi mat.

### Exercise 5.5 - Test stateless

Muc tieu test:

1. Gui request tao conversation.
2. Kill mot instance bat ky.
3. Gui tiep request voi cung session.
4. Kiem tra history van con.

Ket qua da ghi nhan trong qua trinh hoan thien:

- Part 5 direct stateless smoke test pass cho conversation 2 turn.
- Loi off-by-one cua `turn` trong Part 5 production da duoc sua de request dau tien la turn 1.

### Checkpoint Part 5

- Da co health/readiness checks.
- Da co graceful shutdown.
- Da refactor state theo huong Redis/stateless.
- Da hieu Nginx load balancing.
- Da co direct smoke test cho stateless behavior.

## 8. Part 6 - Final Project: Production-Ready AI Agent

### Yeu cau chinh

Final project phai ket hop tat ca concept:

- REST API cho AI agent.
- Conversation history.
- Dockerized multi-stage build.
- Config tu environment variables.
- API key authentication.
- Rate limiting 10 req/min.
- Cost guard 10 USD/thang/user.
- Health check va readiness check.
- Graceful shutdown.
- Stateless design voi Redis.
- Structured JSON logging.
- Render deployment config.

### Cau truc final

```text
06-lab-complete/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── rate_limiter.py
│   ├── cost_guard.py
│   ├── storage.py
│   └── mock_llm.py
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── render.yaml
├── railway.toml
├── .env.example
├── .dockerignore
├── requirements.txt
└── check_production_ready.py
```

### Cac endpoint final

| Endpoint | Method | Auth | Muc dich |
|---|---|---|---|
| `/` | GET | Khong | Thong tin app va endpoint |
| `/health` | GET | Khong | Liveness check |
| `/ready` | GET | Khong | Readiness check |
| `/ask` | POST | `X-API-Key` | Hoi AI agent |
| `/sessions/{session_id}/history` | GET | `X-API-Key` | Xem conversation history |
| `/sessions/{session_id}` | DELETE | `X-API-Key` | Xoa session |
| `/metrics` | GET | `X-API-Key` | Xem request/error/usage metrics |

### Test local final project

Chay Docker Compose:

```bash
cd 06-lab-complete
cp .env.example .env
docker compose up --scale agent=3
```

Test health:

```bash
curl http://localhost/health
```

Test ask:

```bash
curl -X POST http://localhost/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is production deployment?","session_id":"demo"}'
```

Luu y: API key thuc te lay tu `.env` local hoac Render dashboard. Khong nen commit `.env`.

### Ket qua readiness check

Lenh da chay:

```bash
cd 06-lab-complete
python check_production_ready.py
```

Ket qua:

```text
Result: 20/20 checks passed (100%)
```

Nhung muc pass:

- Dockerfile ton tai.
- docker-compose.yml ton tai.
- `.dockerignore` ton tai.
- `.env.example` ton tai.
- requirements.txt ton tai.
- railway.toml hoac render.yaml ton tai.
- `.env` nam trong `.gitignore`.
- Khong co hardcoded secrets trong code chinh.
- Co `/health`.
- Co `/ready`.
- Co authentication.
- Co rate limiting.
- Co graceful shutdown/SIGTERM.
- Co structured JSON logging.
- Dockerfile multi-stage.
- Chay non-root user.
- Co HEALTHCHECK.
- Dung slim base image.
- `.dockerignore` bao gom `.env`.
- `.dockerignore` bao gom `__pycache__`.

### Docker image

Ket qua da ghi nhan:

- Image final `day12-agent-test` build thanh cong.
- Runtime import OK.
- Kich thuoc khoang 71 MB.
- Dat yeu cau image < 500 MB.

## 9. Bao Cao Deployment Render

### Nen tang da chon

Nen tang chon: Render.

Ly do:

- Phu hop yeu cau cua bai.
- Co Blueprint de khai bao infrastructure bang code.
- Co free plan cho lab.
- Co health check, logs, env vars, auto deploy tu GitHub.
- Co Render Key Value de thay Redis cho stateless storage.

### File deployment chinh

File:

```text
06-lab-complete/render.yaml
```

Service:

- Web service: `ai-agent-production`
- Runtime: Docker
- Region: Singapore
- Health check path: `/health`
- Graceful shutdown delay: 30 seconds
- Auto deploy: commit
- Key Value/Redis: `ai-agent-redis`

### Environment variables can co

| Bien | Gia tri/nguon | Muc dich |
|---|---|---|
| `ENVIRONMENT` | `production` | Bat che do production |
| `APP_VERSION` | `1.0.0` | Theo doi version |
| `LOG_LEVEL` | `INFO` | Logging |
| `OPENAI_API_KEY` | Secret, optional | Dung LLM that neu can |
| `AGENT_API_KEY` | Render generate | Bao ve API |
| `JWT_SECRET` | Render generate | Secret cho token/JWT neu dung |
| `RATE_LIMIT_PER_MINUTE` | `10` | Gioi han request |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window rate limit |
| `MONTHLY_BUDGET_USD` | `10.0` | Budget moi user |
| `REDIS_HOST` | From Key Value service | Ket noi Redis |
| `REDIS_PORT` | From Key Value service | Ket noi Redis |

### Public URL

Trang thai hien tai:

```text
Chua co public URL trong phien local nay vi chua dang nhap va deploy tren tai khoan Render.
```

Sau khi deploy, bo sung:

```text
Public URL: https://<ten-service>.onrender.com
```

### Lenh test public URL

Health:

```bash
curl https://<ten-service>.onrender.com/health
```

Expected:

```json
{
  "status": "ok"
}
```

Auth required:

```bash
curl -X POST https://<ten-service>.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
```

Expected:

```text
401 Unauthorized
```

Ask with API key:

```bash
curl -X POST https://<ten-service>.onrender.com/ask \
  -H "X-API-Key: <AGENT_API_KEY_TREN_RENDER>" \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain Render deployment","session_id":"demo"}'
```

Rate limit:

```bash
for i in {1..15}; do
  curl -X POST https://<ten-service>.onrender.com/ask \
    -H "X-API-Key: <AGENT_API_KEY_TREN_RENDER>" \
    -H "Content-Type: application/json" \
    -d "{\"question\":\"test $i\",\"session_id\":\"rate-test\"}"
  echo ""
done
```

Expected:

```text
Sau 10 requests/phut, API tra ve 429 Too Many Requests.
```

## 10. Nhung Dieu Da Hoc Duoc

### Kien thuc co ban

- Web API voi FastAPI.
- Endpoint GET/POST.
- JSON request/response.
- Environment variables.
- `.env.example` va tranh commit `.env`.
- Docker image/container.
- Docker Compose.
- Health check va readiness check.

### Kien thuc nang cao

- 12-Factor App.
- Multi-stage Docker build.
- Non-root container user.
- Reverse proxy/load balancing voi Nginx.
- Stateless app voi Redis.
- Sliding-window rate limiting.
- Monthly budget guard.
- Structured JSON logging.
- Graceful shutdown khi container nhan SIGTERM.
- Cloud deployment bang Render Blueprint.

### Cong cu va thu vien

| Cong cu/thu vien | Dung de lam gi |
|---|---|
| Python 3.11 | Runtime ngon ngu |
| FastAPI | Xay REST API |
| Uvicorn | ASGI server |
| Pydantic/Pydantic Settings | Validate data va config |
| Redis | Luu state chung: rate limit, cost, history |
| Docker | Dong goi app |
| Docker Compose | Chay nhieu service local |
| Nginx | Reverse proxy/load balancing |
| Render | Deploy cloud |
| curl/Postman | Test API |
| Git/GitHub | Quan ly source code va ket noi Render |

## 11. Danh Gia Theo Checklist Nop Bai

| Yeu cau | Trang thai | Ghi chu |
|---|---|---|
| Mission answers | Da tong hop trong file nay | Gom Part 1-6 |
| Full source code Lab 06 | Da co | `06-lab-complete` |
| Multi-stage Dockerfile | Dat | Image final khoang 71 MB |
| API key authentication | Dat | `06-lab-complete/app/auth.py` |
| Rate limiting 10 req/min | Dat | Redis-backed |
| Cost guard 10 USD/month | Dat | Redis-backed |
| Health + readiness | Dat | `/health`, `/ready` |
| Graceful shutdown | Dat | SIGTERM handler |
| Stateless design | Dat | Redis cho history/rate/budget |
| No hardcoded secrets | Dat theo checker | Dung env vars |
| Render config | Dat | `06-lab-complete/render.yaml` |
| Public URL | Chua co trong local | Can deploy tren tai khoan Render |
| Screenshots | Chua co trong local | Can chup dashboard sau khi deploy |

## 12. Ket Luan

Repo Day 12 da duoc hoan thien theo huong production-ready va uu tien Render. Cac phan tu Part 1 den Part 5 da duoc doc, tong hop va kiem chung muc can thiet. Final project trong `06-lab-complete` da tich hop cac yeu cau chinh: Docker multi-stage, config qua env vars, API key authentication, rate limiting, cost guard, health/readiness checks, graceful shutdown, Redis-backed stateless storage va Render deployment config.

Ket qua quan trong nhat:

- `06-lab-complete/check_production_ready.py`: 20/20 checks passed.
- Final Docker image build thanh cong va khoang 71 MB.
- Render duoc chon la nen tang deploy chinh.
- Can thuc hien buoc cuoi tren web Render: dang nhap, connect GitHub repo, deploy Blueprint va bo sung public URL/screenshot.

## 13. Tai Lieu Tham Khao

- Render Web Services: https://render.com/docs/web-services
- Render FastAPI deployment: https://render.com/docs/deploy-fastapi
- Render Environment Variables: https://render.com/docs/configure-environment-variables
- Render Blueprint Specification: https://render.com/docs/blueprint-spec
- Render Logging: https://render.com/docs/logging
- Render Free Plan: https://render.com/docs/free
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- 12-Factor App: https://12factor.net/

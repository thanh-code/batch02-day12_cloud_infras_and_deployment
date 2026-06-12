# Hướng Dẫn Render Cho Người Mới - Deploy Và Show App Trên Web

> File này dành cho người chưa từng đăng nhập Render, chưa từng deploy web service. Mục tiêu là giúp bạn hiểu Render là gì, cách đăng ký, cách deploy app trong repo này lên web, cách test URL public, cách xem logs và cách sửa lỗi cơ bản.

Nguồn chính thức nên đọc thêm:

- Render Web Services: https://render.com/docs/web-services
- Render FastAPI deployment: https://render.com/docs/deploy-fastapi
- Render environment variables: https://render.com/docs/configure-environment-variables
- Render Blueprint spec: https://render.com/docs/blueprint-spec
- Render logs: https://render.com/docs/logging
- Render free instances: https://render.com/docs/free

---

## 1. Render Là Gì?

Render là một cloud platform dùng để đưa ứng dụng lên internet.

Thay vì bạn chạy app trên máy bằng:

```bash
python app.py
```

Render sẽ:

1. Lấy code từ GitHub.
2. Cài dependencies.
3. Chạy app bằng start command.
4. Cấp cho app một URL public dạng:

```text
https://ten-service.onrender.com
```

5. Theo dõi logs, deploy history, health check.

Nói ngắn gọn:

```text
Local app -> GitHub -> Render -> Public URL
```

Trong repo này, Render được dùng để deploy FastAPI AI agent.

---

## 2. Render Giúp Bạn Học Gì?

Render không chỉ là "nút deploy". Nó giúp bạn học các khái niệm production:

| Khái niệm | Ý nghĩa |
|---|---|
| Web Service | App web/API chạy public trên internet |
| Build Command | Lệnh cài đặt/build trước khi app chạy |
| Start Command | Lệnh khởi động server |
| Environment Variables | Biến cấu hình/secret trên cloud |
| Health Check | Endpoint Render dùng để biết app còn sống |
| Logs | Nơi xem lỗi build, lỗi runtime, request |
| Auto Deploy | Tự deploy lại khi bạn push code lên GitHub |
| Blueprint | File `render.yaml` mô tả infrastructure bằng code |

---

## 3. Bạn Cần Chuẩn Bị Gì?

### Tài khoản cần có

- Một tài khoản email.
- Một tài khoản GitHub.
- Một tài khoản Render.

### Trên máy local

Bạn nên có:

- Git.
- Python 3.11+.
- Repo Day 12 này.
- Code đã chạy local ít nhất một lần.

### Folder nên deploy trước

Để học Render cơ bản, dùng folder đơn giản này:

```text
03-cloud-deployment/render/
├── app.py
├── requirements.txt
└── render.yaml
```

Folder này đã được làm tự chứa, dễ deploy hơn `06-lab-complete`.

---

## 4. Hiểu App Render Demo Trong Repo

File:

```text
03-cloud-deployment/render/app.py
```

App này dùng FastAPI và có các endpoint:

| Endpoint | Method | Dùng để |
|---|---|---|
| `/` | GET | Xem app chạy chưa |
| `/health` | GET | Health check cho Render |
| `/ask` | POST | Gửi câu hỏi cho mock AI agent |
| `/docs` | GET | Swagger UI tự động của FastAPI |

Render sẽ chạy app bằng command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Giải thích:

- `uvicorn`: server chạy FastAPI.
- `app:app`: file `app.py`, biến FastAPI tên `app`.
- `--host 0.0.0.0`: cho phép internet truy cập vào container/service.
- `--port $PORT`: dùng port Render cấp qua environment variable.

Nếu bạn hardcode port hoặc chỉ bind `localhost`, app thường deploy fail.

---

## 5. Bước 1 - Tạo Tài Khoản Render

1. Mở: https://render.com
2. Bấm `Get Started` hoặc `Sign Up`.
3. Đăng ký bằng GitHub là dễ nhất.
4. Render sẽ hỏi quyền truy cập GitHub.
5. Cho phép Render đọc repo bạn muốn deploy.

Ghi chú:

- Nếu repo private, bạn phải cho Render quyền truy cập repo đó.
- Nếu repo public, bạn vẫn có thể deploy qua public repository URL, nhưng connect GitHub tiện hơn vì có auto deploy.

---

## 6. Bước 2 - Đưa Code Lên GitHub

Render cần lấy code từ GitHub/GitLab/Bitbucket hoặc public Git URL.

Nếu repo của bạn chưa lên GitHub, làm như sau:

### 6.1 Tạo repo mới trên GitHub

1. Vào https://github.com
2. Bấm `New repository`.
3. Đặt tên, ví dụ:

```text
day12-agent-deployment
```

4. Chọn Public hoặc Private.
5. Không cần tạo README nếu repo local đã có file.

### 6.2 Push code local lên GitHub

Từ thư mục repo:

```bash
git init
git add .
git commit -m "Day 12 deployment lab"
git branch -M main
git remote add origin https://github.com/<your-username>/day12-agent-deployment.git
git push -u origin main
```

Nếu repo đã có git rồi, chỉ cần:

```bash
git add .
git commit -m "Prepare Render deployment"
git push
```

Không commit các file secret:

```text
.env
.env.local
.env.production
```

---

## 7. Cách Deploy Dễ Nhất - New Web Service

Đây là cách nên dùng lần đầu vì bạn nhìn rõ từng field.

### 7.1 Tạo Web Service

1. Vào Render Dashboard:

```text
https://dashboard.render.com
```

2. Bấm `New`.
3. Chọn `Web Service`.
4. Chọn `Git Provider`.
5. Connect GitHub nếu Render hỏi.
6. Chọn repo chứa bài lab.

Theo tài liệu Render, Web Service có thể deploy từ linked Git provider, public Git repo hoặc Docker image. Với bài này, chọn GitHub repo là dễ nhất.

### 7.2 Điền thông tin service

Bạn sẽ thấy form cấu hình. Với folder demo `03-cloud-deployment/render`, điền như sau:

| Field | Giá trị nên nhập |
|---|---|
| Name | `ai-agent-render` |
| Region | `Singapore` nếu có, vì gần Việt Nam |
| Branch | `main` |
| Root Directory | `03-cloud-deployment/render` |
| Runtime / Language | `Python` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free nếu chỉ học cơ bản |
| Health Check Path | `/health` |

Quan trọng nhất:

```text
Root Directory = 03-cloud-deployment/render
```

Nếu quên field này, Render sẽ chạy từ root repo và không thấy đúng `requirements.txt`/`app.py`.

### 7.3 Environment Variables

Trong phần `Environment`, thêm:

```text
ENVIRONMENT=production
PYTHON_VERSION=3.11
```

Nếu app cần API key:

```text
AGENT_API_KEY=<một key bí mật>
OPENAI_API_KEY=<key thật nếu dùng OpenAI thật>
```

Với app demo hiện tại, bạn chưa cần OpenAI key vì dùng mock response.

Theo tài liệu Render, environment variables dùng để cấu hình app theo từng môi trường và tránh commit secret vào source code.

### 7.4 Deploy

1. Bấm `Create Web Service`.
2. Render sẽ bắt đầu build.
3. Bạn sẽ thấy log chạy kiểu:

```text
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port $PORT
```

4. Khi deploy thành công, Render hiển thị URL:

```text
https://ai-agent-render.onrender.com
```

Tên URL thực tế có thể khác tùy service name.

---

## 8. Cách Deploy Bài Bản - Blueprint `render.yaml`

Sau khi hiểu Dashboard, bạn nên học Blueprint.

Blueprint nghĩa là khai báo service bằng file YAML thay vì click thủ công.

Trong repo có:

```text
03-cloud-deployment/render/render.yaml
```

Nội dung chính:

```yaml
services:
  - type: web
    name: ai-agent-render
    runtime: python
    region: singapore
    plan: free
    rootDir: 03-cloud-deployment/render
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeployTrigger: commit
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: PYTHON_VERSION
        value: "3.11"
      - key: AGENT_API_KEY
        generateValue: true
```

Giải thích:

| Field | Nghĩa |
|---|---|
| `type: web` | Tạo Web Service public |
| `name` | Tên service trên Render |
| `runtime: python` | Render dùng Python runtime |
| `region` | Region chạy service |
| `plan` | Gói chạy, demo dùng free |
| `rootDir` | Thư mục chứa app cần build |
| `buildCommand` | Lệnh cài dependencies |
| `startCommand` | Lệnh start server |
| `healthCheckPath` | Endpoint health check |
| `autoDeployTrigger: commit` | Push commit thì auto deploy |
| `envVars` | Biến môi trường |
| `generateValue` | Render tự sinh secret |

### Deploy bằng Blueprint

1. Vào Render Dashboard.
2. Bấm `New`.
3. Chọn `Blueprint`.
4. Connect GitHub repo.
5. Chọn file:

```text
03-cloud-deployment/render/render.yaml
```

6. Review service.
7. Bấm deploy/apply.

Nếu Render mặc định tìm `render.yaml` ở root repo, hãy chọn/customize đường dẫn blueprint trong bước setup.

---

## 9. Cách Show App Trên Web Sau Khi Deploy

Sau khi Render deploy xong, bạn có URL public.

Ví dụ:

```text
https://ai-agent-render.onrender.com
```

### 9.1 Test bằng trình duyệt

Mở các URL sau:

```text
https://ai-agent-render.onrender.com/
https://ai-agent-render.onrender.com/health
https://ai-agent-render.onrender.com/docs
```

Kỳ vọng:

`/` trả JSON kiểu:

```json
{
  "message": "AI Agent running on Render!",
  "platform": "Render",
  "docs": "/docs",
  "health": "/health"
}
```

`/health` trả:

```json
{
  "status": "ok",
  "platform": "Render",
  "uptime_seconds": 123.4
}
```

`/docs` mở Swagger UI của FastAPI.

### 9.2 Test `/ask` bằng Swagger UI

1. Mở:

```text
https://ai-agent-render.onrender.com/docs
```

2. Tìm endpoint:

```text
POST /ask
```

3. Bấm `Try it out`.
4. Nhập body:

```json
{
  "question": "What is Render?"
}
```

5. Bấm `Execute`.
6. Kết quả sẽ có `answer`, `platform`, `timestamp`.

Đây là cách "show trên web" dễ nhất vì không cần Postman hay terminal.

### 9.3 Test bằng curl

Nếu dùng terminal:

```bash
curl https://ai-agent-render.onrender.com/health
```

Gửi câu hỏi:

```bash
curl https://ai-agent-render.onrender.com/ask \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Render?"}'
```

Nhớ thay domain bằng URL thật của bạn.

---

## 10. Xem Logs Trên Render

Logs giúp biết app build fail hay runtime fail.

### Cách xem logs

1. Vào Render Dashboard.
2. Chọn service của bạn.
3. Vào tab `Logs`.
4. Nếu đang deploy, xem tab `Events` hoặc deploy log.

Trong logs, bạn cần tìm:

```text
Build successful
Application startup complete
Uvicorn running on http://0.0.0.0:<port>
```

Nếu lỗi, logs thường có:

```text
ModuleNotFoundError
No open ports detected
Application exited early
Health check failed
```

Theo tài liệu Render, Log Explorer hỗ trợ lọc theo time range/live tail, log level, instance, method, status code, host và path.

---

## 11. Environment Variables Trên Render

Environment variables là nơi lưu config và secret.

### Cách thêm env var

1. Vào Render Dashboard.
2. Chọn service.
3. Chọn tab `Environment`.
4. Bấm `Add Environment Variable`.
5. Nhập key/value.
6. Chọn save/redeploy.

Ví dụ:

```text
ENVIRONMENT=production
LOG_LEVEL=INFO
AGENT_API_KEY=my-secret-key
OPENAI_API_KEY=sk-...
```

Không nên hardcode secret trong code:

```python
OPENAI_API_KEY = "sk-..."
```

Nên đọc từ env:

```python
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
```

### Khi nào cần redeploy?

Nếu bạn đổi env var:

- `Save, rebuild, and deploy`: build lại và deploy.
- `Save and deploy`: deploy lại bản build hiện có với env mới.
- `Save only`: lưu nhưng chưa áp dụng cho service đang chạy.

---

## 12. Health Check Là Gì?

Render dùng health check để biết service có còn sống không.

Trong demo:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

Trong Render:

```yaml
healthCheckPath: /health
```

Nếu `/health` lỗi, timeout hoặc trả non-200, Render có thể coi deploy/service là unhealthy.

Endpoint health nên:

- Nhanh.
- Không yêu cầu authentication.
- Không gọi LLM thật.
- Không tốn tiền.
- Trả `200` khi process sống.

---

## 13. `$PORT` Và `0.0.0.0` Là Gì?

Đây là lỗi người mới rất hay gặp.

Render cấp port cho service qua env var:

```text
PORT
```

Vì vậy command đúng:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Sai thường gặp:

```bash
uvicorn app:app --host localhost --port 8000
```

Vì:

- `localhost` chỉ nghe trong container/service, internet không vào được.
- `8000` có thể không phải port Render đang route.

Theo tài liệu Render, web service phải bind vào `0.0.0.0` để nhận HTTP request public.

---

## 14. Auto Deploy Là Gì?

Khi service connect GitHub, Render có thể tự deploy khi bạn push commit.

Flow:

```text
Sửa code local -> git commit -> git push -> Render tự build/deploy
```

Nếu dùng Blueprint trong repo:

```yaml
autoDeployTrigger: commit
```

Nghĩa là commit mới có thể kích hoạt deploy mới.

Khi học, auto deploy rất tiện. Khi production thật, đôi khi team sẽ tắt auto deploy và deploy thủ công sau khi test.

---

## 15. Deploy App Hoàn Chỉnh `06-lab-complete`

Sau khi hiểu app demo, bạn có thể deploy final project:

```text
06-lab-complete/
├── Dockerfile
├── render.yaml
├── app/
├── requirements.txt
└── ...
```

File:

```text
06-lab-complete/render.yaml
```

Khác với demo Part 3:

- Dùng `runtime: docker`.
- Có Redis-compatible Render Key Value service.
- Có `AGENT_API_KEY`, `JWT_SECRET`, budget, rate limit.
- Có `REDIS_HOST`, `REDIS_PORT` từ service `ai-agent-redis`.

Bạn nên deploy `03-cloud-deployment/render` trước để hiểu căn bản, rồi mới deploy `06-lab-complete`.

---

## 16. Các Lỗi Hay Gặp Và Cách Sửa

### Lỗi 1: Render không tìm thấy `requirements.txt`

Nguyên nhân:

- Chưa set đúng `Root Directory`.

Cách sửa:

```text
Root Directory = 03-cloud-deployment/render
```

Hoặc trong Blueprint:

```yaml
rootDir: 03-cloud-deployment/render
```

---

### Lỗi 2: `ModuleNotFoundError: No module named ...`

Nguyên nhân:

- Build command không cài đúng dependencies.
- `requirements.txt` thiếu package.
- Start command chạy sai module.

Cách sửa:

Kiểm tra:

```text
Build Command = pip install -r requirements.txt
Start Command = uvicorn app:app --host 0.0.0.0 --port $PORT
```

Với `app.py` chứa:

```python
app = FastAPI()
```

Thì start command là:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Nếu file là `main.py`, command có thể là:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Nếu package là `app/main.py`, command có thể là:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

### Lỗi 3: No open ports detected

Nguyên nhân thường gặp:

- App không bind `0.0.0.0`.
- App không dùng `$PORT`.
- App crash trước khi server start.

Cách sửa:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

---

### Lỗi 4: Health check failed

Nguyên nhân:

- Không có endpoint `/health`.
- `/health` trả lỗi.
- Health path trong Render sai.
- App startup quá lâu.

Cách sửa:

Trong FastAPI:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

Trong Render:

```text
Health Check Path = /health
```

---

### Lỗi 5: Mở `/ask` trên browser bị lỗi

`/ask` là POST endpoint, browser address bar gửi GET.

Cách test đúng:

- Dùng `/docs`.
- Dùng curl.
- Dùng Postman.

Swagger UI:

```text
https://your-app.onrender.com/docs
```

---

### Lỗi 6: App Free bị chậm lần đầu

Nếu dùng free instance, app có thể có giới hạn tài nguyên hoặc cold start tùy chính sách hiện tại của Render. Hãy xem tài liệu free instances của Render để biết giới hạn mới nhất.

Khi học, chậm lần đầu không hẳn là lỗi app.

---

## 17. Checklist Deploy Render Lần Đầu

Trước khi bấm deploy:

- [ ] Code đã push lên GitHub.
- [ ] Có `requirements.txt`.
- [ ] Có FastAPI object tên `app`.
- [ ] Có endpoint `/health`.
- [ ] Start command dùng `0.0.0.0`.
- [ ] Start command dùng `$PORT`.
- [ ] Root directory đúng.
- [ ] Không commit `.env`.
- [ ] Secret nằm trong Render Environment.

Sau khi deploy:

- [ ] Mở được public URL `/`.
- [ ] Mở được `/health`.
- [ ] Mở được `/docs`.
- [ ] Test được `POST /ask`.
- [ ] Xem được logs.
- [ ] Biết redeploy khi push code.

---

## 18. Lộ Trình Học Render Theo Repo Này

### Bước 1: Deploy app demo đơn giản

Folder:

```text
03-cloud-deployment/render
```

Mục tiêu:

- Hiểu Root Directory.
- Hiểu Build/Start command.
- Có public URL.
- Test `/health`, `/ask`, `/docs`.

### Bước 2: Đọc `render.yaml`

Mục tiêu:

- Hiểu Blueprint.
- Biết infrastructure as code là gì.
- Biết không hardcode secret.

### Bước 3: Deploy final agent

Folder:

```text
06-lab-complete
```

Mục tiêu:

- Docker runtime.
- Redis/Key Value.
- Auth.
- Rate limit.
- Cost guard.
- Health/readiness.

### Bước 4: Quan sát logs và sửa lỗi

Mục tiêu:

- Đọc build log.
- Đọc runtime log.
- Test public URL.
- Biết rollback/redeploy nếu cần.

---

## 19. Ghi Nhớ Nhanh

Render cần 4 thứ chính:

```text
1. Code trên GitHub
2. Build Command
3. Start Command
4. App listen đúng host/port
```

Với FastAPI demo:

```text
Root Directory: 03-cloud-deployment/render
Build Command: pip install -r requirements.txt
Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

Test sau deploy:

```text
https://your-app.onrender.com/
https://your-app.onrender.com/health
https://your-app.onrender.com/docs
```

Nếu 3 URL này chạy, bạn đã "show app lên web" thành công.


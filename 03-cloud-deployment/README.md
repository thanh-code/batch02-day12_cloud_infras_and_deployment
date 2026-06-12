# Section 3 - Cloud Deployment Options

## Render First

Render is the preferred platform for this lab. The `render/` folder contains a self-contained FastAPI app plus a Render Blueprint.

```
render/
├── app.py
├── requirements.txt
└── render.yaml
```

### Deploy Render

1. Push this repository to GitHub.
2. Render Dashboard -> New -> Blueprint.
3. Connect the repository.
4. Use `03-cloud-deployment/render/render.yaml` as the blueprint.
5. Render builds from `rootDir: 03-cloud-deployment/render`.
6. Test the public URL:

```bash
curl https://<your-render-url>/health
curl https://<your-render-url>/ask \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Render?"}'
```

## Railway Reference

Railway is kept as a reference/prototype option.

```
railway/
├── railway.toml
├── app.py
├── requirements.txt
└── utils/mock_llm.py
```

Basic flow:

```bash
cd railway
railway login
railway init
railway up
railway domain
```

## Cloud Run Reference

`production-cloud-run/` contains GCP Cloud Run configuration for a more production-oriented CI/CD path.

```
production-cloud-run/
├── cloudbuild.yaml
└── service.yaml
```

## Discussion

1. Why is Render Blueprint easier to review than manual dashboard setup?
2. What is cold start and how can it affect an AI agent?
3. When would you move from Render to Cloud Run?

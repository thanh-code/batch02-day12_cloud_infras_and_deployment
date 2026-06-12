# Implementation Plan - Lab 12 Complete Agent

## Context Read

- Main task comes from `CODE_LAB.md`, Part 6: build a production-ready AI agent combining Docker, cloud deployment, API security, rate limiting, cost guard, health checks, readiness checks, graceful shutdown, stateless storage, and structured logging.
- `README.md` points to `06-lab-complete` as the final deliverable folder.
- `06-lab-complete/README.md` lists the expected complete structure and readiness checklist.
- Cloud deployment choice: use Render, so `render.yaml` is the primary deployment configuration. Railway files can remain as reference, but the final implementation should be Render-ready.

## Current Gaps Found

- `app/main.py` currently mixes auth, rate limiting, cost guard, and app logic in one file.
- Rate limiting and budget tracking are in memory, which breaks stateless scaling across multiple instances.
- Conversation history is not implemented.
- `app/auth.py`, `app/rate_limiter.py`, and `app/cost_guard.py` are missing even though the lab structure requires them.
- Dockerfile copies `utils/`, but `06-lab-complete` does not contain a `utils` directory, so Docker build can fail when using this folder as the build context.
- `docker-compose.yml` has agent and Redis but no Nginx load balancer service.
- `render.yaml` exists but should be aligned with the final environment variable names and Render deployment path.

## Implementation Steps

1. Keep configuration 12-factor in `app/config.py`.
   - Add monthly budget and conversation history settings.
   - Keep production validation for required secrets.

2. Make the app self-contained.
   - Add a local mock LLM module under `app/`.
   - Stop depending on a missing `utils/` folder in the Docker build context.

3. Split production concerns into modules.
   - `app/auth.py`: validate `X-API-Key` and return a stable user id.
   - `app/rate_limiter.py`: Redis-backed sliding window rate limiting with an in-memory fallback for local development.
   - `app/cost_guard.py`: Redis-backed monthly per-user budget tracking with estimated token costs.

4. Refactor `app/main.py`.
   - Use the new modules.
   - Add conversation history stored in Redis when available.
   - Keep `/health`, `/ready`, `/metrics`, and `/ask`.
   - Return session id, served-by instance id, budget usage, and rate limit metadata.
   - Preserve structured JSON logging and graceful shutdown behavior.

5. Complete local scaling infrastructure.
   - Add `nginx.conf`.
   - Update `docker-compose.yml` with `nginx`, `agent`, and `redis`.

6. Update Docker and Render deployment.
   - Make Dockerfile copy only files that exist in `06-lab-complete`.
   - Keep multi-stage build, non-root runtime user, and health check.
   - Update `render.yaml` with Render as the selected cloud platform and required env vars.

7. Verify.
   - Run `python check_production_ready.py`.
   - Run import/syntax checks.
   - If feasible in this environment, run a local FastAPI smoke test without requiring external network.

## Completion Notes

- Implemented the plan in `06-lab-complete`.
- Render is the selected deploy target in `render.yaml`.
- Docker image `day12-agent-test` builds successfully and is about 71 MB.
- `check_production_ready.py` passes 20/20 checks.
- Direct app smoke test passes for missing-key auth, valid-key ask flow, usage tracking, and session history.

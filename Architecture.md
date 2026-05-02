# DevCollab — Enterprise Architecture Specification
**For Claude Code · Vue 3 + FastAPI · GCP Cloud Run · MongoDB Atlas · Redis · Google Services**

---

## 1. Project overview

Build a team collaboration and communication platform for software/dev teams. The platform simplifies workflows and improves task visibility. It runs entirely on GCP, deployed via Cloud Run, and uses Google-managed services wherever possible.

**Primary goals:**
- Real-time task visibility across sprints and projects
- Simplified team communication (channels, DMs, threads)
- Developer-specific integrations (GitHub, CI status, code snippets)
- Enterprise-grade security, observability, and scalability

---

## 2. Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Pinia, Vue Router, Vite, TailwindCSS |
| Backend | Python 3.12, FastAPI, Uvicorn |
| Primary DB | MongoDB Atlas (VPC-peered to GCP) |
| Cache / Presence | GCP Memorystore (Redis 7) |
| Real-time client push | Firestore (client SDK) |
| Auth | Google Identity Platform (Firebase Auth) |
| File storage | GCP Cloud Storage |
| Async jobs | GCP Cloud Tasks + Cloud Run worker |
| Messaging bus | GCP Cloud Pub/Sub |
| Static hosting | Firebase Hosting (Vue SPA) |
| CDN + LB | GCP Cloud CDN + HTTP(S) Load Balancer |
| Security | Cloud Armor (WAF/DDoS), Cloud KMS, Secret Manager |
| Observability | Cloud Monitoring, Cloud Logging, Cloud Trace |
| CI/CD | Cloud Build + Artifact Registry |
| Container runtime | Cloud Run (asia-south1) |

---

## 3. Repository structure

```
devcollab/
├── frontend/                        # Vue 3 SPA
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/                  # Pinia stores
│   │   │   ├── auth.ts
│   │   │   ├── workspace.ts
│   │   │   ├── tasks.ts
│   │   │   ├── messages.ts
│   │   │   └── presence.ts
│   │   ├── composables/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useFirestore.ts
│   │   │   └── useAuth.ts
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── SprintBoard.vue
│   │   │   ├── Channel.vue
│   │   │   ├── DirectMessage.vue
│   │   │   ├── Roadmap.vue
│   │   │   └── Settings.vue
│   │   ├── components/
│   │   │   ├── kanban/
│   │   │   │   ├── KanbanBoard.vue
│   │   │   │   ├── KanbanColumn.vue
│   │   │   │   └── TaskCard.vue
│   │   │   ├── chat/
│   │   │   │   ├── MessageList.vue
│   │   │   │   ├── MessageInput.vue
│   │   │   │   └── ThreadPanel.vue
│   │   │   ├── tasks/
│   │   │   │   ├── TaskDetail.vue
│   │   │   │   ├── TaskForm.vue
│   │   │   │   └── TaskFilters.vue
│   │   │   └── shared/
│   │   │       ├── Avatar.vue
│   │   │       ├── PresenceDot.vue
│   │   │       └── Sidebar.vue
│   │   └── lib/
│   │       ├── api.ts               # Axios instance + interceptors
│   │       ├── firebase.ts          # Firebase SDK init
│   │       └── constants.ts
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── Dockerfile
│   └── .firebaserc
│
├── backend/
│   ├── services/
│   │   ├── api-gateway/             # Cloud Run service 1
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── auth.py
│   │   │   │   ├── workspaces.py
│   │   │   │   └── users.py
│   │   │   ├── middleware/
│   │   │   │   ├── auth_middleware.py
│   │   │   │   └── rate_limiter.py
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── task-service/            # Cloud Run service 2
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── tasks.py
│   │   │   │   ├── sprints.py
│   │   │   │   └── projects.py
│   │   │   ├── models/
│   │   │   │   ├── task.py
│   │   │   │   ├── sprint.py
│   │   │   │   └── project.py
│   │   │   ├── services/
│   │   │   │   ├── task_service.py
│   │   │   │   ├── cache_service.py  # Redis cache layer
│   │   │   │   └── firestore_sync.py # Firestore mirror writes
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── messaging-service/       # Cloud Run service 3
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── channels.py
│   │   │   │   ├── messages.py
│   │   │   │   └── websocket.py
│   │   │   ├── services/
│   │   │   │   ├── pubsub_service.py
│   │   │   │   └── presence_service.py
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   └── notification-worker/     # Cloud Run service 4 (jobs)
│   │       ├── main.py
│   │       ├── handlers/
│   │       │   ├── email_handler.py
│   │       │   ├── push_handler.py
│   │       │   └── digest_handler.py
│   │       ├── Dockerfile
│   │       └── requirements.txt
│   │
│   └── shared/                      # Shared Python package
│       ├── __init__.py
│       ├── db.py                    # MongoDB motor client
│       ├── redis_client.py          # Redis aioredis client
│       ├── pubsub_client.py         # GCP Pub/Sub client
│       ├── firestore_client.py      # Firestore admin client
│       ├── gcs_client.py            # Cloud Storage client
│       ├── auth.py                  # JWT verification helpers
│       ├── models/
│       │   └── base.py
│       └── config.py                # Settings via Secret Manager
│
├── infra/                           # Infrastructure as code
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── modules/
│   │   │   ├── cloud_run/
│   │   │   ├── memorystore/
│   │   │   ├── pubsub/
│   │   │   ├── cloud_storage/
│   │   │   └── vpc/
│   │   └── environments/
│   │       ├── staging.tfvars
│   │       └── production.tfvars
│   └── cloudbuild/
│       ├── cloudbuild.yaml          # Main CI/CD pipeline
│       └── deploy.sh
│
├── docker-compose.yml               # Local dev environment
└── README.md
```

---

## 4. MongoDB Atlas schema

All collections live in the `devcollab` database. Use the `workspace_id` field as the primary shard key across all collections.

### Collection: `workspaces`
```json
{
  "_id": "ObjectId",
  "name": "string",
  "slug": "string (unique)",
  "plan": "free | pro | enterprise",
  "owner_id": "ObjectId ref users",
  "members": [
    { "user_id": "ObjectId", "role": "admin | member | guest", "joined_at": "ISODate" }
  ],
  "settings": {
    "allowed_domains": ["string"],
    "sso_enabled": "boolean",
    "github_org": "string"
  },
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### Collection: `users`
```json
{
  "_id": "ObjectId",
  "firebase_uid": "string (unique)",
  "email": "string",
  "display_name": "string",
  "avatar_url": "string (GCS path)",
  "workspace_ids": ["ObjectId"],
  "notification_prefs": {
    "email_digest": "none | daily | weekly",
    "push_enabled": "boolean",
    "mention_only": "boolean"
  },
  "created_at": "ISODate"
}
```

### Collection: `tasks`
```json
{
  "_id": "ObjectId",
  "workspace_id": "ObjectId",
  "project_id": "ObjectId",
  "sprint_id": "ObjectId | null",
  "title": "string",
  "description": "string (markdown)",
  "type": "task | bug | story | epic",
  "status": "backlog | todo | in_progress | review | done",
  "priority": "low | medium | high | critical",
  "assignee_ids": ["ObjectId"],
  "reporter_id": "ObjectId",
  "labels": ["string"],
  "story_points": "number",
  "due_date": "ISODate | null",
  "github_pr_urls": ["string"],
  "comments": [
    {
      "id": "ObjectId",
      "author_id": "ObjectId",
      "body": "string",
      "created_at": "ISODate"
    }
  ],
  "attachments": [
    { "name": "string", "gcs_path": "string", "size": "number" }
  ],
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### Collection: `messages`
```json
{
  "_id": "ObjectId",
  "workspace_id": "ObjectId",
  "channel_id": "ObjectId",
  "author_id": "ObjectId",
  "body": "string",
  "thread_id": "ObjectId | null",
  "mentions": ["ObjectId"],
  "attachments": ["string"],
  "reactions": [{ "emoji": "string", "user_ids": ["ObjectId"] }],
  "edited": "boolean",
  "created_at": "ISODate"
}
```

### Collection: `channels`
```json
{
  "_id": "ObjectId",
  "workspace_id": "ObjectId",
  "name": "string",
  "type": "public | private | dm",
  "member_ids": ["ObjectId"],
  "topic": "string",
  "created_at": "ISODate"
}
```

### Collection: `projects`
```json
{
  "_id": "ObjectId",
  "workspace_id": "ObjectId",
  "name": "string",
  "color": "string",
  "github_repo": "string | null",
  "created_at": "ISODate"
}
```

### Collection: `sprints`
```json
{
  "_id": "ObjectId",
  "workspace_id": "ObjectId",
  "project_id": "ObjectId",
  "name": "string",
  "goal": "string",
  "start_date": "ISODate",
  "end_date": "ISODate",
  "status": "planned | active | completed",
  "velocity": "number"
}
```

### Collection: `activity_logs`
```json
{
  "_id": "ObjectId",
  "workspace_id": "ObjectId",
  "actor_id": "ObjectId",
  "action": "task.created | task.moved | task.assigned | message.sent | sprint.started | ...",
  "entity_type": "task | message | sprint | project",
  "entity_id": "ObjectId",
  "meta": {},
  "created_at": "ISODate"
}
```

### Required MongoDB indexes
```javascript
// tasks collection
db.tasks.createIndex({ workspace_id: 1, status: 1 })
db.tasks.createIndex({ workspace_id: 1, sprint_id: 1 })
db.tasks.createIndex({ workspace_id: 1, assignee_ids: 1 })
db.tasks.createIndex({ workspace_id: 1, updated_at: -1 })

// messages collection
db.messages.createIndex({ channel_id: 1, created_at: -1 })
db.messages.createIndex({ workspace_id: 1, author_id: 1 })

// activity_logs collection
db.activity_logs.createIndex({ workspace_id: 1, created_at: -1 })
db.activity_logs.createIndex({ entity_id: 1 })
```

---

## 5. Redis (Memorystore) key design

```
# Session / auth
session:{user_id}                    → JWT refresh token  TTL: 7d
user_presence:{workspace_id}         → Hash {user_id: "online|away|offline|timestamp"}  TTL: 30s (heartbeat refresh)

# Task cache
sprint_board:{workspace_id}:{sprint_id}  → JSON serialized board state  TTL: 5min
task:{task_id}                           → JSON serialized task  TTL: 10min

# Rate limiting
rate:{user_id}:{endpoint}            → request count  TTL: 60s

# WebSocket room membership
ws_room:{workspace_id}               → Set of connection IDs
```

**Cache invalidation rules:**
- On `PATCH /tasks/{id}` → `DEL task:{task_id}`, `DEL sprint_board:{workspace_id}:{sprint_id}`
- On `POST /tasks` → `DEL sprint_board:{workspace_id}:{sprint_id}`
- On workspace member join/leave → update `user_presence:{workspace_id}`

---

## 6. Firestore structure (real-time client sync)

Firestore is used for pushing real-time state to Vue clients via the Firebase client SDK. It mirrors critical hot state from MongoDB.

```
/workspaces/{workspace_id}/
  presence/                          # Online presence map
    {user_id}: { status, last_seen, display_name, avatar_url }

  task_updates/                      # Latest task state changes (rolling window)
    {task_id}: { status, assignee_ids, updated_at, updated_by }

  notifications/                     # Per-user notification queue
    {user_id}/items/{notif_id}: { type, title, body, read, created_at }
```

**Write pattern:** FastAPI backend writes to Firestore via Admin SDK on every task status change and new message. Vue client subscribes via `onSnapshot()`. This gives instant UI updates without polling.

---

## 7. FastAPI service implementations

### 7.1 Shared config (`backend/shared/config.py`)
```python
from pydantic_settings import BaseSettings
from google.cloud import secretmanager

class Settings(BaseSettings):
    project_id: str
    mongodb_uri: str          # fetched from Secret Manager
    redis_host: str
    redis_port: int = 6379
    pubsub_project: str
    gcs_bucket: str
    firebase_project_id: str
    allowed_origins: list[str]
    environment: str = "production"

    @classmethod
    def from_secret_manager(cls):
        client = secretmanager.SecretManagerServiceClient()
        # fetch secrets by name, return cls instance
        ...

settings = Settings.from_secret_manager()
```

### 7.2 MongoDB motor client (`backend/shared/db.py`)
```python
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

_client: AsyncIOMotorClient | None = None

async def get_db():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client["devcollab"]

async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None
```

### 7.3 Task service router (`backend/services/task-service/routers/tasks.py`)
```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from bson import ObjectId
from shared.db import get_db
from shared.redis_client import get_redis
from shared.firestore_client import sync_task_to_firestore
from shared.pubsub_client import publish_event
from ..models.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/{workspace_id}")
async def list_tasks(workspace_id: str, sprint_id: str | None = None,
                     status: str | None = None, db=Depends(get_db), redis=Depends(get_redis)):
    cache_key = f"sprint_board:{workspace_id}:{sprint_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    query = {"workspace_id": ObjectId(workspace_id)}
    if sprint_id:
        query["sprint_id"] = ObjectId(sprint_id)
    if status:
        query["status"] = status

    tasks = await db["tasks"].find(query).sort("updated_at", -1).to_list(200)
    result = [TaskResponse.from_mongo(t) for t in tasks]

    await redis.setex(cache_key, 300, json.dumps([r.dict() for r in result]))
    return result

@router.patch("/{task_id}")
async def update_task(task_id: str, payload: TaskUpdate, bg: BackgroundTasks,
                      db=Depends(get_db), redis=Depends(get_redis)):
    update_data = payload.dict(exclude_none=True)
    update_data["updated_at"] = datetime.utcnow()

    result = await db["tasks"].find_one_and_update(
        {"_id": ObjectId(task_id)},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(404, "Task not found")

    # Invalidate cache
    await redis.delete(f"task:{task_id}")
    await redis.delete(f"sprint_board:{result['workspace_id']}:{result.get('sprint_id')}")

    # Async: sync to Firestore + publish event
    bg.add_task(sync_task_to_firestore, result)
    bg.add_task(publish_event, "task.updated", result)

    return TaskResponse.from_mongo(result)
```

### 7.4 WebSocket messaging (`backend/services/messaging-service/routers/websocket.py`)
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.cloud import pubsub_v1
import asyncio, json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, workspace_id: str):
        await ws.accept()
        self.connections.setdefault(workspace_id, []).append(ws)

    def disconnect(self, ws: WebSocket, workspace_id: str):
        conns = self.connections.get(workspace_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, workspace_id: str, message: dict):
        for ws in self.connections.get(workspace_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(ws: WebSocket, workspace_id: str):
    await manager.connect(ws, workspace_id)
    # Subscribe to Pub/Sub topic for this workspace
    subscriber = pubsub_v1.SubscriberClient()
    subscription = f"projects/{PROJECT_ID}/subscriptions/ws-{workspace_id}"
    asyncio.create_task(pubsub_listener(subscriber, subscription, workspace_id))
    try:
        while True:
            data = await ws.receive_json()
            # handle ping/pong, typing indicators
            await handle_client_message(data, workspace_id, ws)
    except WebSocketDisconnect:
        manager.disconnect(ws, workspace_id)

async def pubsub_listener(subscriber, subscription, workspace_id):
    # Pull messages from Pub/Sub and broadcast to all WS connections in workspace
    ...
```

### 7.5 Auth middleware (`backend/services/api-gateway/middleware/auth_middleware.py`)
```python
from fastapi import Request, HTTPException
from firebase_admin import auth as firebase_auth
import firebase_admin

app_firebase = firebase_admin.initialize_app()

async def verify_firebase_token(request: Request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split(" ")[1]
    try:
        decoded = firebase_auth.verify_id_token(token)
        request.state.user_id = decoded["uid"]
        request.state.email = decoded.get("email")
        return decoded
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
```

---

## 8. Vue 3 frontend

### 8.1 Firebase init (`frontend/src/lib/firebase.ts`)
```typescript
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const db = getFirestore(app)
export const googleProvider = new GoogleAuthProvider()
```

### 8.2 Auth store (`frontend/src/stores/auth.ts`)
```typescript
import { defineStore } from 'pinia'
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth'
import { auth, googleProvider } from '@/lib/firebase'
import api from '@/lib/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as any,
    token: null as string | null,
    loading: true,
  }),
  actions: {
    async loginWithGoogle() {
      const result = await signInWithPopup(auth, googleProvider)
      const token = await result.user.getIdToken()
      this.token = token
      this.user = result.user
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    },
    async logout() {
      await signOut(auth)
      this.user = null
      this.token = null
    },
    init() {
      onAuthStateChanged(auth, async (user) => {
        this.user = user
        if (user) {
          this.token = await user.getIdToken()
          api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        }
        this.loading = false
      })
    }
  }
})
```

### 8.3 Task store with Firestore real-time sync (`frontend/src/stores/tasks.ts`)
```typescript
import { defineStore } from 'pinia'
import { collection, onSnapshot, query, where } from 'firebase/firestore'
import { db } from '@/lib/firebase'
import api from '@/lib/api'

export const useTaskStore = defineStore('tasks', {
  state: () => ({
    tasks: [] as Task[],
    loading: false,
  }),
  actions: {
    async fetchTasks(workspaceId: string, sprintId: string) {
      this.loading = true
      const { data } = await api.get(`/tasks/${workspaceId}`, { params: { sprint_id: sprintId } })
      this.tasks = data
      this.loading = false
    },
    subscribeToUpdates(workspaceId: string) {
      // Firestore real-time subscription for live task status updates
      const q = query(
        collection(db, `workspaces/${workspaceId}/task_updates`)
      )
      return onSnapshot(q, (snapshot) => {
        snapshot.docChanges().forEach((change) => {
          const updated = change.doc.data()
          const idx = this.tasks.findIndex(t => t._id === change.doc.id)
          if (idx !== -1) {
            this.tasks[idx] = { ...this.tasks[idx], ...updated }
          }
        })
      })
    },
    async moveTask(taskId: string, newStatus: string) {
      await api.patch(`/tasks/${taskId}`, { status: newStatus })
      // Optimistic update — Firestore subscription will confirm
      const task = this.tasks.find(t => t._id === taskId)
      if (task) task.status = newStatus
    }
  }
})
```

### 8.4 WebSocket composable (`frontend/src/composables/useWebSocket.ts`)
```typescript
import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function useWebSocket(workspaceId: string) {
  const ws = ref<WebSocket | null>(null)
  const messages = ref<any[]>([])
  const authStore = useAuthStore()

  function connect() {
    const url = `${import.meta.env.VITE_WS_URL}/ws/${workspaceId}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      ws.value!.send(JSON.stringify({ type: 'auth', token: authStore.token }))
    }

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      messages.value.push(data)
    }

    ws.value.onclose = () => {
      // Reconnect with exponential backoff
      setTimeout(connect, 2000)
    }
  }

  function send(payload: object) {
    ws.value?.send(JSON.stringify(payload))
  }

  connect()
  onUnmounted(() => ws.value?.close())

  return { messages, send }
}
```

---

## 9. GCP infrastructure

### 9.1 Cloud Run service configuration (per service)
```yaml
# cloud-run-service.yaml template
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: devcollab-task-service
  annotations:
    run.googleapis.com/ingress: internal-and-cloud-load-balancing
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "50"
        run.googleapis.com/vpc-access-connector: devcollab-vpc-connector
        run.googleapis.com/vpc-access-egress: private-ranges-only
    spec:
      serviceAccountName: devcollab-task-sa@PROJECT_ID.iam.gserviceaccount.com
      containerConcurrency: 80
      containers:
        - image: REGION-docker.pkg.dev/PROJECT_ID/devcollab/task-service:latest
          ports:
            - containerPort: 8080
          env:
            - name: ENVIRONMENT
              value: production
            - name: GCP_PROJECT_ID
              value: PROJECT_ID
          resources:
            limits:
              memory: 512Mi
              cpu: "1"
          livenessProbe:
            httpGet:
              path: /health
            initialDelaySeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
```

### 9.2 Cloud Build CI/CD (`infra/cloudbuild/cloudbuild.yaml`)
```yaml
steps:
  # Run tests
  - name: python:3.12
    entrypoint: pip
    args: [install, -r, backend/services/task-service/requirements.txt]
  - name: python:3.12
    entrypoint: pytest
    args: [backend/services/task-service/tests/]

  # Build and push Docker images
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - -t
      - ${_REGION}-docker.pkg.dev/${PROJECT_ID}/devcollab/task-service:${SHORT_SHA}
      - backend/services/task-service/

  - name: gcr.io/cloud-builders/docker
    args: [push, ${_REGION}-docker.pkg.dev/${PROJECT_ID}/devcollab/task-service:${SHORT_SHA}]

  # Deploy to Cloud Run
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    entrypoint: gcloud
    args:
      - run
      - deploy
      - devcollab-task-service
      - --image=${_REGION}-docker.pkg.dev/${PROJECT_ID}/devcollab/task-service:${SHORT_SHA}
      - --region=${_REGION}
      - --platform=managed
      - --no-traffic  # blue/green: send traffic after health check

substitutions:
  _REGION: asia-south1

options:
  logging: CLOUD_LOGGING_ONLY
```

### 9.3 Dockerfile template (all FastAPI services)
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ../../shared /app/shared

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

### 9.4 Frontend Dockerfile
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## 10. IAM and service accounts

```
devcollab-gateway-sa     → roles/run.invoker, roles/secretmanager.secretAccessor
devcollab-task-sa        → roles/datastore.user, roles/secretmanager.secretAccessor, roles/pubsub.publisher
devcollab-messaging-sa   → roles/pubsub.subscriber, roles/pubsub.publisher, roles/secretmanager.secretAccessor
devcollab-worker-sa      → roles/cloudtasks.enqueuer, roles/secretmanager.secretAccessor
devcollab-build-sa       → roles/artifactregistry.writer, roles/run.admin, roles/iam.serviceAccountUser
```

**Principle of least privilege:** each service account can only access the specific GCP services it needs. No service account has `owner` or `editor` roles.

---

## 11. Environment variables and secrets

All secrets are stored in **GCP Secret Manager** and fetched at startup. Never put secrets in environment variables or code.

| Secret name | Description |
|---|---|
| `devcollab-mongodb-uri` | MongoDB Atlas connection string |
| `devcollab-redis-host` | Memorystore Redis private IP |
| `devcollab-firebase-credentials` | Firebase Admin SDK service account JSON |
| `devcollab-github-webhook-secret` | GitHub webhook HMAC secret |
| `devcollab-sendgrid-api-key` | SendGrid API key for email |

**Frontend env vars** (non-secret, in `.env.production`):
```
VITE_API_URL=https://api.devcollab.yourdomain.com
VITE_WS_URL=wss://ws.devcollab.yourdomain.com
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
```

---

## 12. GCP Pub/Sub topics and subscriptions

```
Topic: devcollab-task-events
  Subscription: task-service-sub      → task-service Cloud Run (push)
  Subscription: ws-broadcast-sub      → messaging-service Cloud Run (pull, per workspace)
  Subscription: activity-log-sub      → notification-worker (push)

Topic: devcollab-notification-events
  Subscription: email-notif-sub       → notification-worker (push)
  Subscription: push-notif-sub        → notification-worker (push)

Topic: devcollab-presence-events
  Subscription: presence-sub          → messaging-service (pull, heartbeat)
```

---

## 13. Local development setup

```yaml
# docker-compose.yml
version: '3.9'
services:
  mongo:
    image: mongo:7
    ports: ["27017:27017"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      - VITE_API_URL=http://localhost:8001
      - VITE_WS_URL=ws://localhost:8002
    volumes:
      - ./frontend/src:/app/src

  task-service:
    build: ./backend/services/task-service
    ports: ["8001:8080"]
    environment:
      - MONGODB_URI=mongodb://mongo:27017/devcollab
      - REDIS_HOST=redis
      - ENVIRONMENT=development
    depends_on: [mongo, redis]

  messaging-service:
    build: ./backend/services/messaging-service
    ports: ["8002:8080"]
    environment:
      - MONGODB_URI=mongodb://mongo:27017/devcollab
      - REDIS_HOST=redis
      - ENVIRONMENT=development
    depends_on: [mongo, redis]
```

---

## 14. Build order for Claude Code

Implement in this exact sequence:

1. `infra/` — Terraform VPC, Memorystore, Pub/Sub topics, Cloud Storage bucket, Secret Manager secrets
2. `backend/shared/` — DB client, Redis client, Pub/Sub client, Firestore client, config, auth helpers
3. `backend/services/api-gateway/` — FastAPI app, auth middleware, rate limiter, workspace/user routers
4. `backend/services/task-service/` — tasks, sprints, projects routers + cache layer + Firestore sync
5. `backend/services/messaging-service/` — channels, messages, WebSocket endpoint + Pub/Sub listener
6. `backend/services/notification-worker/` — Cloud Tasks handler, email + push handlers
7. `frontend/src/lib/` — Firebase init, Axios API client
8. `frontend/src/stores/` — auth, workspace, tasks, messages, presence Pinia stores
9. `frontend/src/composables/` — useWebSocket, useFirestore, useAuth
10. `frontend/src/views/` — Dashboard, SprintBoard, Channel, DirectMessage, Roadmap
11. `frontend/src/components/` — KanbanBoard with drag-and-drop (Vue Draggable), MessageList, TaskDetail
12. `infra/cloudbuild/` — CI/CD pipeline, Dockerfiles for all services
13. `docker-compose.yml` — local dev environment wiring all services

---

## 15. Key architectural decisions

- **Cloud Run over GKE** — simpler ops, scales to zero, per-request billing, no cluster management
- **MongoDB Atlas over Firestore for primary DB** — richer query language, aggregations, flexible schema
- **Firestore for real-time client push only** — cheapest and simplest way to push state to Vue clients without polling; Atlas Change Streams are the backend trigger
- **Memorystore Redis** — fully managed, VPC-native, no patching; used for hot cache + presence, not as the WS pub/sub bus (Pub/Sub handles cross-instance fan-out)
- **Cloud Pub/Sub for WS broadcast** — Cloud Run instances don't share memory; Pub/Sub ensures every instance broadcasting to a workspace gets the event
- **Firebase Auth** — eliminates building auth from scratch; Google SSO built in; JWT verified server-side via Firebase Admin SDK
- **Cloud Tasks for async jobs** — retries, rate limiting, and dead-letter queues built in; better than a raw Celery/Redis queue for GCP-native deployments

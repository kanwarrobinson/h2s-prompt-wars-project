#!/usr/bin/env bash
# Manual deployment script for DevCollab services
set -euo pipefail

REGION="${REGION:-asia-south1}"
PROJECT_ID="${PROJECT_ID:?PROJECT_ID environment variable required}"
ENVIRONMENT="${ENVIRONMENT:-production}"
SHA="${SHA:-$(git rev-parse --short HEAD)}"

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/devcollab"

SERVICES=(
  "api-gateway:backend/services/api-gateway"
  "task-service:backend/services/task-service"
  "messaging-service:backend/services/messaging-service"
  "notification-worker:backend/services/notification-worker"
  "frontend:frontend"
)

echo "🚀 Deploying DevCollab to ${ENVIRONMENT} (project: ${PROJECT_ID}, region: ${REGION})"

for entry in "${SERVICES[@]}"; do
  NAME="${entry%%:*}"
  CONTEXT="${entry##*:}"
  IMAGE="${REGISTRY}/${NAME}:${SHA}"

  echo "📦 Building ${NAME}..."
  if [[ "${CONTEXT}" == backend/* ]]; then
    docker build -t "${IMAGE}" -f "${CONTEXT}/Dockerfile" backend/
  else
    docker build -t "${IMAGE}" "${CONTEXT}/"
  fi

  echo "⬆️  Pushing ${NAME}..."
  docker push "${IMAGE}"

  echo "🌐 Deploying ${NAME} to Cloud Run..."
  gcloud run deploy "devcollab-${NAME}" \
    --image="${IMAGE}" \
    --region="${REGION}" \
    --platform=managed \
    --project="${PROJECT_ID}" \
    --no-traffic \
    --tag="sha-${SHA}"

  echo "🔀 Migrating traffic for ${NAME}..."
  gcloud run services update-traffic "devcollab-${NAME}" \
    --to-tags="sha-${SHA}=100" \
    --region="${REGION}" \
    --project="${PROJECT_ID}"

  echo "✅ ${NAME} deployed"
done

echo "🎉 All services deployed successfully!"

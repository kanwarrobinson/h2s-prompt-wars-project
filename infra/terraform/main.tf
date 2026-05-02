terraform {
  required_version = ">= 1.8"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "devcollab-tf-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "redis.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "cloudtasks.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# Artifact Registry
resource "google_artifact_registry_repository" "devcollab" {
  location      = var.artifact_registry_region
  repository_id = "devcollab"
  format        = "DOCKER"
  description   = "DevCollab Docker images"
  depends_on    = [google_project_service.apis]
}

# VPC module
module "vpc" {
  source      = "./modules/vpc"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

# Memorystore Redis
module "redis" {
  source         = "./modules/memorystore"
  project_id     = var.project_id
  region         = var.region
  environment    = var.environment
  memory_size_gb = var.redis_memory_size_gb
  network        = module.vpc.network_id
  depends_on     = [google_project_service.apis, module.vpc]
}

# Pub/Sub topics and subscriptions
module "pubsub" {
  source      = "./modules/pubsub"
  project_id  = var.project_id
  environment = var.environment
  depends_on  = [google_project_service.apis]
}

# Cloud Storage bucket
module "storage" {
  source      = "./modules/cloud_storage"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  depends_on  = [google_project_service.apis]
}

# Service Accounts
resource "google_service_account" "gateway_sa" {
  account_id   = "devcollab-gateway-sa"
  display_name = "DevCollab API Gateway Service Account"
}

resource "google_service_account" "task_sa" {
  account_id   = "devcollab-task-sa"
  display_name = "DevCollab Task Service Account"
}

resource "google_service_account" "messaging_sa" {
  account_id   = "devcollab-messaging-sa"
  display_name = "DevCollab Messaging Service Account"
}

resource "google_service_account" "worker_sa" {
  account_id   = "devcollab-worker-sa"
  display_name = "DevCollab Worker Service Account"
}

resource "google_service_account" "build_sa" {
  account_id   = "devcollab-build-sa"
  display_name = "DevCollab Cloud Build Service Account"
}

# IAM bindings (principle of least privilege)
locals {
  sa_roles = {
    (google_service_account.gateway_sa.email) = [
      "roles/run.invoker",
      "roles/secretmanager.secretAccessor",
    ]
    (google_service_account.task_sa.email) = [
      "roles/datastore.user",
      "roles/secretmanager.secretAccessor",
      "roles/pubsub.publisher",
    ]
    (google_service_account.messaging_sa.email) = [
      "roles/pubsub.subscriber",
      "roles/pubsub.publisher",
      "roles/secretmanager.secretAccessor",
    ]
    (google_service_account.worker_sa.email) = [
      "roles/cloudtasks.enqueuer",
      "roles/secretmanager.secretAccessor",
    ]
    (google_service_account.build_sa.email) = [
      "roles/artifactregistry.writer",
      "roles/run.admin",
      "roles/iam.serviceAccountUser",
    ]
  }
}

resource "google_project_iam_member" "sa_roles" {
  for_each = {
    for pair in flatten([
      for sa, roles in local.sa_roles : [
        for role in roles : { sa = sa, role = role }
      ]
    ]) : "${pair.sa}-${pair.role}" => pair
  }
  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${each.value.sa}"
}

# Secret Manager secrets (names only — values set out-of-band)
resource "google_secret_manager_secret" "secrets" {
  for_each = toset([
    "devcollab-mongodb-uri",
    "devcollab-redis-host",
    "devcollab-firebase-credentials",
    "devcollab-github-webhook-secret",
    "devcollab-sendgrid-api-key",
  ])
  secret_id = each.value
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

# Cloud Run services
module "api_gateway" {
  source          = "./modules/cloud_run"
  project_id      = var.project_id
  region          = var.region
  service_name    = "devcollab-api-gateway"
  image           = "${var.artifact_registry_region}-docker.pkg.dev/${var.project_id}/devcollab/api-gateway:latest"
  service_account = google_service_account.gateway_sa.email
  vpc_connector   = module.vpc.vpc_connector_id
  min_instances   = var.min_instances
  max_instances   = var.max_instances
  environment     = var.environment
  env_vars = {
    ENVIRONMENT            = var.environment
    GCP_PROJECT_ID         = var.project_id
    SECRET_MANAGER_ENABLED = "true"
  }
  depends_on = [module.vpc, google_artifact_registry_repository.devcollab]
}

module "task_service" {
  source          = "./modules/cloud_run"
  project_id      = var.project_id
  region          = var.region
  service_name    = "devcollab-task-service"
  image           = "${var.artifact_registry_region}-docker.pkg.dev/${var.project_id}/devcollab/task-service:latest"
  service_account = google_service_account.task_sa.email
  vpc_connector   = module.vpc.vpc_connector_id
  min_instances   = var.min_instances
  max_instances   = var.max_instances
  environment     = var.environment
  env_vars = {
    ENVIRONMENT            = var.environment
    GCP_PROJECT_ID         = var.project_id
    SECRET_MANAGER_ENABLED = "true"
  }
  depends_on = [module.vpc, google_artifact_registry_repository.devcollab]
}

module "messaging_service" {
  source          = "./modules/cloud_run"
  project_id      = var.project_id
  region          = var.region
  service_name    = "devcollab-messaging-service"
  image           = "${var.artifact_registry_region}-docker.pkg.dev/${var.project_id}/devcollab/messaging-service:latest"
  service_account = google_service_account.messaging_sa.email
  vpc_connector   = module.vpc.vpc_connector_id
  min_instances   = var.min_instances
  max_instances   = var.max_instances
  environment     = var.environment
  env_vars = {
    ENVIRONMENT            = var.environment
    GCP_PROJECT_ID         = var.project_id
    SECRET_MANAGER_ENABLED = "true"
  }
  depends_on = [module.vpc, google_artifact_registry_repository.devcollab]
}

module "notification_worker" {
  source          = "./modules/cloud_run"
  project_id      = var.project_id
  region          = var.region
  service_name    = "devcollab-notification-worker"
  image           = "${var.artifact_registry_region}-docker.pkg.dev/${var.project_id}/devcollab/notification-worker:latest"
  service_account = google_service_account.worker_sa.email
  vpc_connector   = module.vpc.vpc_connector_id
  min_instances   = 0
  max_instances   = 10
  environment     = var.environment
  env_vars = {
    ENVIRONMENT            = var.environment
    GCP_PROJECT_ID         = var.project_id
    SECRET_MANAGER_ENABLED = "true"
  }
  depends_on = [module.vpc, google_artifact_registry_repository.devcollab]
}

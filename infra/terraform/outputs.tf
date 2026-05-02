output "api_gateway_url" {
  description = "API Gateway Cloud Run URL"
  value       = module.api_gateway.service_url
}

output "task_service_url" {
  description = "Task Service Cloud Run URL"
  value       = module.task_service.service_url
}

output "messaging_service_url" {
  description = "Messaging Service Cloud Run URL"
  value       = module.messaging_service.service_url
}

output "notification_worker_url" {
  description = "Notification Worker Cloud Run URL"
  value       = module.notification_worker.service_url
}

output "redis_host" {
  description = "Memorystore Redis private IP"
  value       = module.redis.host
  sensitive   = true
}

output "gcs_bucket_name" {
  description = "GCS uploads bucket name"
  value       = module.storage.bucket_name
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = "${var.artifact_registry_region}-docker.pkg.dev/${var.project_id}/devcollab"
}

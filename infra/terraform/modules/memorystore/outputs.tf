output "host" {
  description = "Redis instance private IP address"
  value       = google_redis_instance.cache.host
  sensitive   = true
}

output "port" {
  description = "Redis instance port"
  value       = google_redis_instance.cache.port
}

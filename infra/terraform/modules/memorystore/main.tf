resource "google_redis_instance" "cache" {
  name               = "devcollab-${var.environment}-redis"
  tier               = "STANDARD_HA"
  memory_size_gb     = var.memory_size_gb
  region             = var.region
  project            = var.project_id
  authorized_network = var.network
  redis_version      = "REDIS_7_0"
  display_name       = "DevCollab Cache"

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 2
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }
}

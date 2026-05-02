locals {
  topics = {
    "devcollab-task-events"         = {}
    "devcollab-notification-events" = {}
    "devcollab-presence-events"     = {}
  }

  subscriptions = {
    "task-service-sub" = {
      topic        = "devcollab-task-events"
      ack_deadline = 60
      push_endpoint = null
    }
    "ws-broadcast-sub" = {
      topic        = "devcollab-task-events"
      ack_deadline = 30
      push_endpoint = null
    }
    "activity-log-sub" = {
      topic        = "devcollab-task-events"
      ack_deadline = 60
      push_endpoint = null
    }
    "email-notif-sub" = {
      topic        = "devcollab-notification-events"
      ack_deadline = 120
      push_endpoint = null
    }
    "push-notif-sub" = {
      topic        = "devcollab-notification-events"
      ack_deadline = 60
      push_endpoint = null
    }
    "presence-sub" = {
      topic        = "devcollab-presence-events"
      ack_deadline = 30
      push_endpoint = null
    }
  }
}

resource "google_pubsub_topic" "topics" {
  for_each = local.topics
  name     = each.key
  project  = var.project_id

  message_retention_duration = "86600s"
}

resource "google_pubsub_subscription" "subscriptions" {
  for_each = local.subscriptions
  name     = each.key
  topic    = google_pubsub_topic.topics[each.value.topic].name
  project  = var.project_id

  ack_deadline_seconds       = each.value.ack_deadline
  message_retention_duration = "86400s"
  retain_acked_messages      = false

  expiration_policy {
    ttl = ""
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

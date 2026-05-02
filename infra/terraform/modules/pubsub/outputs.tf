output "topic_ids" {
  description = "Map of topic names to IDs"
  value       = { for k, v in google_pubsub_topic.topics : k => v.id }
}

output "subscription_ids" {
  description = "Map of subscription names to IDs"
  value       = { for k, v in google_pubsub_subscription.subscriptions : k => v.id }
}

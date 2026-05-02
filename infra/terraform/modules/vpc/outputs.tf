output "network_id" {
  description = "VPC network self-link"
  value       = google_compute_network.vpc.id
}

output "subnet_id" {
  description = "Private subnetwork self-link"
  value       = google_compute_subnetwork.private.id
}

output "vpc_connector_id" {
  description = "Serverless VPC Access connector ID"
  value       = google_vpc_access_connector.connector.id
}

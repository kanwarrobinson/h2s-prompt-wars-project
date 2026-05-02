output "bucket_name" {
  description = "GCS uploads bucket name"
  value       = google_storage_bucket.uploads.name
}

output "bucket_url" {
  description = "GCS uploads bucket URL"
  value       = google_storage_bucket.uploads.url
}

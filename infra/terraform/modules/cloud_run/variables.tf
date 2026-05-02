variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "image" {
  description = "Docker image URI"
  type        = string
}

variable "service_account" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "vpc_connector" {
  description = "Serverless VPC Access connector ID"
  type        = string
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "environment" {
  description = "Environment: staging or production"
  type        = string
}

variable "env_vars" {
  description = "Environment variables to set on the container"
  type        = map(string)
  default     = {}
}

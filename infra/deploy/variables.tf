variable "db_instance_tier" {
  description = "tier for database instance VM"
  type        = string
  default     = "db-f1-micro"
}

variable "environment" {
  description = "environment containing resources"
  type        = string
}

variable "project" {
  description = "the ID of the Google project"
  type        = string
}

variable "region" {
  description = "deploy resources in this region"
  type        = string
  default     = "us-east1"
}

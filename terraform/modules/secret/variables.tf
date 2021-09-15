variable "data" {
  description = "the data the secret will hold"
  sensitive   = true
  type        = string
}

variable "id" {
  description = "the id of the secret"
  type        = string
}

variable "members" {
  description = "entities who can access the secret"
  type        = list(string)
}

variable "project" {
  description = "the ID of the Google project"
  type        = string
}

provider "google" {
  project     = var.project
  region      = "us-east1"
  zone        = "us-east1-c"
}

locals {
  product     = "shows"
  name_prefix = join("-", [var.region, var.environment, local.product])
}

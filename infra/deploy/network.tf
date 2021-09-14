resource "google_compute_network" "shows" {
  name = join("-", [local.name_prefix, "nw"])

  auto_create_subnetworks = false
}

resource "google_compute_global_address" "shows" {
  name          = join("-", [local.name_prefix, "private-ip"])
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.shows.id
}

resource "google_service_networking_connection" "shows" {
  network                 = google_compute_network.shows.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.shows.name]
}

// tfsec:ignore:google-compute-enable-vpc-flow-logs
resource "google_compute_subnetwork" "shows" {
  name          = "serverless-access"
  ip_cidr_range = "10.2.0.0/28"
  region        = var.region
  network       = google_compute_network.shows.id
}

resource "google_vpc_access_connector" "shows" {
  provider = google-beta

  name    = "serverless-access"
  project = var.project
  region  = var.region

  subnet {
    name = google_compute_subnetwork.shows.name
  }
}

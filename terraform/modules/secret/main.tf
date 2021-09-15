resource "google_secret_manager_secret" "secret" {
  secret_id = var.id

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "secret" {
  secret = google_secret_manager_secret.secret.id

  secret_data = var.data
}

// tfsec:ignore:general-secrets-sensitive-in-attribute
resource "google_secret_manager_secret_iam_binding" "secret" {
  project   = var.project
  secret_id = google_secret_manager_secret.secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  members = var.members
}

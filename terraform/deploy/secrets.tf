// app engine secrets

data "google_app_engine_default_service_account" "default" {}

resource "google_secret_manager_secret" "database_password" {
  secret_id = "database_password"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "database_password" {
  secret = google_secret_manager_secret.database_password.id

  secret_data = random_password.shows.result
}

resource "google_secret_manager_secret_iam_binding" "app_enging" {
  project   = var.project
  secret_id = google_secret_manager_secret.database_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  members = [
    join(":", ["serviceAccount", data.google_app_engine_default_service_account.default.email])
  ]
}

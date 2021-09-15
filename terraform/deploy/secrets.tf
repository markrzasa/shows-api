// app engine secrets

data "google_app_engine_default_service_account" "default" {}

module "secrets" {
  source = "../modules/secret"

  for_each = {
    database_password       = random_password.shows.result
    database_server_ca_cert = google_sql_ssl_cert.shows.server_ca_cert
    database_client_cert    = google_sql_ssl_cert.shows.cert
    database_private_key    = google_sql_ssl_cert.shows.private_key
  }

  data    = each.value
  id      = each.key
  members = [join(":", ["serviceAccount", data.google_app_engine_default_service_account.default.email])]
  project = var.project
}

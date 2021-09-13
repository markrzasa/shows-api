provider "google" {
  project     = var.project
  region      = "us-east1"
  zone        = "us-east1-c"
}

locals {
  product     = "shows"
  name_prefix = join("-", [var.region, var.environment, local.product])

  python_dir = join("/", [path.root, "..", "..", "python"])
}

resource "random_string" "suffix" {
  length  = 3
  special = false
  upper   = false
}

resource "google_sql_database_instance" "shows" {
  name                = join("-", [local.name_prefix, "db-instance", random_string.suffix.result])
  region              = var.region
  database_version    = "POSTGRES_11"
  deletion_protection = false

  settings {
    tier = var.db_instance_tier
  }
}

resource "google_sql_database" "shows" {
  name = "shows"
  instance = google_sql_database_instance.shows.name
}

resource "random_password" "shows" {
  length = 32
}

resource "google_sql_user" "shows" {
  instance = google_sql_database_instance.shows.name
  name     = "shows"
  password = random_password.shows.result
}

data "archive_file" "app" {
  type = "zip"

  source_dir  = local.python_dir
  output_path = join("/", [path.root, "generated", "app.zip"])
}

resource "google_storage_bucket" "app" {
  name    = join("-", [local.name_prefix, "app"])
  project = var.project

  force_destroy = true
}

resource "google_storage_bucket_object" "app" {
  name   = join(".", ["shows-api-archive", data.archive_file.app.output_md5, "zip"])
  source = data.archive_file.app.output_path
  bucket = google_storage_bucket.app.name
}

//resource "google_app_engine_application" "app" {
//  location_id = var.region
//  project     = var.project
//}

resource "google_app_engine_standard_app_version" "app" {
  depends_on = [google_sql_database.shows]

  runtime    = "python39"
  service    = "default"
  version_id = "v1"

  basic_scaling {
    idle_timeout = "300s"
    max_instances = 1
  }

  deployment {
    zip {
      source_url = "https://storage.googleapis.com/${google_storage_bucket.app.name}/${google_storage_bucket_object.app.name}"
    }
  }

  entrypoint {
    shell = "uvicorn main:app --app-dir app --host 0.0.0.0 --port $${PORT}"
  }

  env_variables = {
    CLOUD_SQL_CONNECTION_NAME = google_sql_database_instance.shows.connection_name

    PROJECT_ID                 = var.project
    SQL_PASS_SECRET_VERSION_ID = google_secret_manager_secret_version.database_password.id

    SQL_DB   = google_sql_database.shows.name
    SQL_HOST = google_sql_database_instance.shows.public_ip_address
    SQL_USER = google_sql_user.shows.name
    SQL_PASS = google_sql_user.shows.password
  }

  noop_on_destroy = true
}

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

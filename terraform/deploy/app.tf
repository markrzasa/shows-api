// deploys the application in app engine

locals {
  python_dir = join("/", [path.root, "..", "..", "python"])
}

data "archive_file" "app" {
  type = "zip"

  source_dir  = local.python_dir
  output_path = join("/", [path.root, "generated", "app.zip"])
}

resource "google_storage_bucket" "app" {
  name    = join("-", [local.name_prefix, "app"])
  project = var.project

  force_destroy               = true
  uniform_bucket_level_access = true
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
    PROJECT_ID                           = var.project
    SQL_SERVER_CA_CERT_SECRET_VERSION_ID = module.secrets["database_server_ca_cert"].secret_version_id
    SQL_CLIENT_CERT_SECRET_VERSION_ID    = module.secrets["database_client_cert"].secret_version_id
    SQL_PRIVATE_KEY_SECRET_VERSION_ID    = module.secrets["database_private_key"].secret_version_id
    SQL_PASS_SECRET_VERSION_ID           = module.secrets["database_password"].secret_version_id
    SQL_DB                               = google_sql_database.shows.name
    SQL_HOST                             = google_sql_database_instance.shows.private_ip_address
    SQL_USER                             = google_sql_user.shows.name
    SQL_SSL_MODE                         = "require"
    SQL_PASS                             = google_sql_user.shows.password
  }

  vpc_access_connector {
    name = google_vpc_access_connector.shows.self_link
  }

  noop_on_destroy = false
}

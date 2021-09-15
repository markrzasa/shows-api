// deploy a database with a private IP

locals {
  database_flags = {
    log_lock_waits     = "on"
    log_checkpoints    = "on"
    log_connections    = "on"
    log_disconnections = "on"
    log_temp_files     = "0"
  }
}

resource "random_string" "suffix" {
  length  = 3
  special = false
  upper   = false
}

// tfsec:ignore:google-sql-enable-backup - the data in this database does not need to be backed up
resource "google_sql_database_instance" "shows" {
  name                = join("-", [local.name_prefix, "db-instance", random_string.suffix.result])
  region              = var.region
  database_version    = "POSTGRES_11"
  deletion_protection = false

  settings {
    tier = var.db_instance_tier

    dynamic "database_flags" {
      for_each = local.database_flags

      content {
        name  = database_flags.key
        value = database_flags.value
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.shows.id
      require_ssl     = true
    }
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

resource "google_sql_ssl_cert" "shows" {
  common_name = "show-app"
  instance    = google_sql_database_instance.shows.name
  project     = var.project
}

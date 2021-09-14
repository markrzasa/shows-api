import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import DatabaseConnection, SQL_PORT, SQL_DB, SQL_USER, SQL_HOST, SQL_PASS, escape_value


class TestDatabaseConnection(unittest.TestCase):
    def setUp(self) -> None:
        DatabaseConnection.close_connection()

    @patch('app.psycopg2')
    @patch('app.secretmanager')
    def test_connect_to_cloud_sql(self, secretmanager, psycopg2):
        client = MagicMock()
        secret = MagicMock()
        secret.payload.data = 'password'.encode('utf-8')
        client.access_secret_version.return_value = secret
        secretmanager.SecretManagerServiceClient.return_value = client
        with patch.dict(os.environ, {
            'CLOUD_SQL_CONNECTION_NAME': 'testing',
            'PROJECT_ID': 'testing',
            'SQL_PASS_SECRET_VERSION_ID': 'test-version'
        }):
            DatabaseConnection.get_connection()
            client.access_secret_version.assert_called_once()
            psycopg2.connect.assert_called_with(
                host='/cloudsql/testing',
                port=SQL_PORT,
                database=SQL_DB,
                user=SQL_USER,
                password='password',
                sslmode='allow'
            )

    @patch('app.psycopg2')
    @patch('app.secretmanager')
    def test_connect_to_sql(self, secretmanager, psycopg2):
        client = MagicMock()
        secretmanager.SecretManagerServiceClient.return_value = client
        DatabaseConnection.get_connection()
        client.access_secret_version.assert_not_called()
        psycopg2.connect.assert_called_with(
            host=SQL_HOST,
            port=SQL_PORT,
            database=SQL_DB,
            user=SQL_USER,
            password=SQL_PASS,
            sslmode='allow'
        )

    def test_escape_value(self):
        self.assertEqual("'don''t'", escape_value("don't"))

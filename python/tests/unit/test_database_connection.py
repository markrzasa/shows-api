import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import DatabaseConnection, SQL_PORT, SQL_DB, SQL_USER, SQL_HOST, SQL_PASS, to_db_value, init_logging


class TestDatabaseConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        init_logging()

    def setUp(self) -> None:
        DatabaseConnection.close_connection()

    @patch('app.psycopg2')
    @patch('app.secretmanager')
    def test_connect_to_cloud_sql(self, secretmanager, psycopg2):
        client = MagicMock()
        secret = MagicMock()
        secret_data = 'top-secret'
        secret.payload.data = secret_data.encode('utf-8')
        client.access_secret_version.return_value = secret
        secretmanager.SecretManagerServiceClient.return_value = client
        with patch.dict(os.environ, {
            'PROJECT_ID': 'testing',
            'SQL_SERVER_CA_CERT_SECRET_VERSION_ID': 'test-version',
            'SQL_CLIENT_CERT_SECRET_VERSION_ID': 'test-version',
            'SQL_PRIVATE_KEY_SECRET_VERSION_ID': 'test-version',
            'SQL_PASS_SECRET_VERSION_ID': 'test-version',
            'SQL_SSL_MODE': 'require'
        }):
            DatabaseConnection.get_connection()
            self.assertEqual(4, client.access_secret_version.call_count)
            _, kwargs = psycopg2.connect.call_args
            self.assertEqual(SQL_HOST, kwargs['host'])
            self.assertEqual(SQL_PORT, kwargs['port'])
            self.assertEqual(SQL_DB, kwargs['database'])
            self.assertEqual(SQL_USER, kwargs['user'])
            self.assertEqual(secret_data, kwargs['password'])
            self.assertEqual('require', kwargs['sslmode'])
            self.assertIsNotNone(kwargs['sslrootcert'])
            self.assertIsNotNone(kwargs['sslcert'])
            self.assertIsNotNone(kwargs['sslkey'])

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
        self.assertEqual("'don''t'", to_db_value("don't"))

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import Engine, SQL_PORT, SQL_DB, SQL_USER, SQL_HOST, SQL_PASS, init_logging


class TestEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        init_logging()

    def tearDown(self) -> None:
        Engine._Engine__engine = None
        Engine._Engine__session = None

    @patch('app.create_engine')
    @patch('app.secretmanager')
    @patch('app.sessionmaker')
    @patch('app.Base')
    def test_connect_to_cloud_sql(self, base, sessionmaker, secretmanager, create_engine):
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
            Engine.get_engine()
            self.assertEqual(4, client.access_secret_version.call_count)
            args, kwargs = create_engine.call_args
            self.assertEqual(f'postgresql+psycopg2://{SQL_USER}:{secret_data}@{SQL_HOST}:{SQL_PORT}/{SQL_DB}', args[0])
            self.assertIn('connect_args', kwargs)
            connect_args = kwargs['connect_args']
            self.assertEqual('require', connect_args['sslmode'])
            self.assertIsNotNone(connect_args['sslrootcert'])
            self.assertIsNotNone(connect_args['sslcert'])
            self.assertIsNotNone(connect_args['sslkey'])
            sessionmaker.assert_called_once()
            base.metadata.create_all.assert_called_once()

    @patch('app.create_engine')
    @patch('app.secretmanager')
    @patch('app.sessionmaker')
    @patch('app.Base')
    def test_connect_to_sql(self, base, sessionmaker, secretmanager, create_engine):
        client = MagicMock()
        secretmanager.SecretManagerServiceClient.return_value = client
        Engine.get_engine()
        client.access_secret_version.assert_not_called()
        create_engine.assert_called_with(f'postgresql+psycopg2://{SQL_USER}:{SQL_PASS}@{SQL_HOST}:{SQL_PORT}/{SQL_DB}')
        sessionmaker.assert_called_once()
        base.metadata.create_all.assert_called_once()

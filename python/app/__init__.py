import logging
import os
import tempfile

import psycopg2
import sys
from google.cloud import secretmanager

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from lib import SQL_COLUMNS

SQL_DB = os.getenv('SQL_DB', 'shows')
SQL_HOST = os.getenv('SQL_HOST', 'localhost')
SQL_PASS = os.getenv('SQL_PASS', 'postgres')
SQL_PORT = os.getenv('SQL_PORT', '5432')
SQL_USER = os.getenv('SQL_USER', 'postgres')

INSERT_COLUMNS = ','.join(SQL_COLUMNS).replace('cast', '"cast"')


class DatabaseConnection:
    __conn = None

    @classmethod
    def get_secret(cls, secret_version_id: str):
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_version_id)
        return response.payload.data.decode("UTF-8")

    @classmethod
    def sql_password(cls):
        sql_pass_secret_version_id = os.getenv('SQL_PASS_SECRET_VERSION_ID')
        if sql_pass_secret_version_id:
            return cls.get_secret(sql_pass_secret_version_id)

        return SQL_PASS

    @classmethod
    def sql_host(cls):
        cloud_sql_connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
        return f'/cloudsql/{cloud_sql_connection_name}' if cloud_sql_connection_name else SQL_HOST

    @classmethod
    def sql_certs(cls):
        return os.getenv('SQL_SERVER_CA_CERT_SECRET_VERSION_ID'),\
            os.getenv('SQL_CLIENT_CERT_SECRET_VERSION_ID'),\
            os.getenv('SQL_PRIVATE_KEY_SECRET_VERSION_ID')

    @classmethod
    def ssl_mode(cls):
        return os.getenv('SQL_SSL_MODE', 'allow')

    @classmethod
    def connect(cls, sql_host):
        root_cert, client_cert, private_key = cls.sql_certs()
        if root_cert and client_cert and private_key:
            logging.info('attempting to establish a secure connection')
            with tempfile.TemporaryDirectory() as root_cert_dir:
                root_cert_file = os.path.join(root_cert_dir, 'root.crt')
                with open(root_cert_file, 'w') as handle:
                    handle.write(cls.get_secret(root_cert))
                client_cert_file = os.path.join(root_cert_dir, 'client.crt')
                with open(client_cert_file, 'w') as handle:
                    handle.write(cls.get_secret(client_cert))
                private_key_file = os.path.join(root_cert_dir, 'private.key')
                with open(private_key_file, 'w') as handle:
                    handle.write(cls.get_secret(private_key))
                os.chmod(private_key_file, 0o600)
                return psycopg2.connect(
                    host=sql_host, port=SQL_PORT, database=SQL_DB,
                    user=SQL_USER, password=cls.sql_password(),
                    sslmode=cls.ssl_mode(), sslrootcert=root_cert_file,
                    sslcert=client_cert_file, sslkey=private_key_file
                )

        return psycopg2.connect(
            host=sql_host, port=SQL_PORT, database=SQL_DB,
            user=SQL_USER, password=cls.sql_password(), sslmode=cls.ssl_mode())

    @classmethod
    def get_connection(cls):
        if not cls.__conn:
            sql_host = cls.sql_host()
            logging.info(f'connecting to database {sql_host}.{SQL_DB}')
            cls.__conn = cls.connect(sql_host)
            logging.info(f'connected to database {SQL_DB}')
            with cls.__conn.cursor() as cursor:
                cursor.execute((
                    'CREATE TABLE IF NOT EXISTS shows ('
                    '  show_id      varchar,'
                    '  type         varchar,'
                    '  title        varchar,'
                    '  director     varchar,'
                    '  "cast"       varchar,'
                    '  country      varchar,'
                    '  date_added   varchar,'
                    '  release_year varchar,'
                    '  rating       varchar,'
                    '  duration     varchar,'
                    '  listed_in    varchar,'
                    '  description  varchar,'
                    '  PRIMARY      KEY(show_id)'
                    ');'))
                cls.__conn.commit()
            logging.info('table ready')

        return cls.__conn

    @classmethod
    def close_connection(cls):
        if cls.__conn:
            logging.info('closing database connection')
            cls.__conn.close()
            cls.__conn = None
            logging.info('closed database connection')


def escape_value(v: str) -> str:
    escaped_v = v.replace("'", "''")
    return f"'{escaped_v}'"


def init_logging():
    logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO, stream=sys.stdout)

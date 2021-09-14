import logging
import os
import psycopg2
import sys
from google.cloud import secretmanager

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from lib import SQL_COLUMNS

SQL_DB = os.getenv('SQL_DB', 'shows')
SQL_HOST = os.getenv('SQL_HOST', 'localhost')
SQL_PASS = os.getenv('SQL_PASS', 'postgres')
SQL_PORT = os.getenv('SQL_PORT', '5432')
SQL_SSL_MODE = os.getenv('SQL_SSL_MODE', 'allow')
SQL_USER = os.getenv('SQL_USER', 'postgres')

INSERT_COLUMNS = ','.join(SQL_COLUMNS).replace('cast', '"cast"')


class DatabaseConnection:
    __conn = None

    @classmethod
    def sql_password(cls):
        cloud_sql_connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
        project_id = os.getenv('PROJECT_ID')
        sql_pass_secret_version_id = os.getenv('SQL_PASS_SECRET_VERSION_ID')

        if cloud_sql_connection_name and project_id and sql_pass_secret_version_id:
            client = secretmanager.SecretManagerServiceClient()
            response = client.access_secret_version(name=sql_pass_secret_version_id)
            return response.payload.data.decode("UTF-8")

        return SQL_PASS

    @classmethod
    def sql_host(cls):
        cloud_sql_connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
        return f'/cloudsql/{cloud_sql_connection_name}' if cloud_sql_connection_name else SQL_HOST

    @classmethod
    def get_connection(cls):
        if not cls.__conn:
            sql_host = cls.sql_host()
            logging.info(f'connecting to database {sql_host}.{SQL_DB}')
            cls.__conn = psycopg2.connect(
                host=sql_host, port=SQL_PORT, database=SQL_DB,
                user=SQL_USER, password=cls.sql_password(), sslmode=SQL_SSL_MODE)
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

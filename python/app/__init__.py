import logging
import os
import tempfile

import sys
from google.cloud import secretmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.persistence import Base

SQL_DB = os.getenv('SQL_DB', 'shows')
SQL_HOST = os.getenv('SQL_HOST', 'localhost')
SQL_PASS = os.getenv('SQL_PASS', 'postgres')
SQL_PORT = os.getenv('SQL_PORT', '5432')
SQL_USER = os.getenv('SQL_USER', 'postgres')

SHOWS_TABLE = 'shows'
LISTED_IN_TABLE = 'listed_in'


class Engine:
    __engine = None
    __session = None

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
    def get_engine(cls):
        if not cls.__engine:
            sql_host = cls.sql_host()
            logging.info(f'connecting to database {sql_host}.{SQL_DB}')
            db_connect_string = f'postgresql+psycopg2://{SQL_USER}:{cls.sql_password()}@{sql_host}:{SQL_PORT}/{SQL_DB}'
            root_cert, client_cert, private_key = cls.sql_certs()
            if root_cert and client_cert and private_key:
                logging.info('attempting to establish a secure connection')
                # If the app has been provisioned with certificates and a key, write the certs and key to temp files to
                # establish a connection. The temporary files will be removed when the code leaves the with block.
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
                    create_engine(db_connect_string, connect_args={
                        'sslmode': cls.ssl_mode(),
                        'sslrootcert': root_cert_file,
                        'sslcert': client_cert_file,
                        'sslkey': private_key_file
                    })
            else:
                cls.__engine = create_engine(db_connect_string)
            if not cls.__session:
                cls.__session = sessionmaker(cls.__engine)
                Base.metadata.create_all(cls.__engine)

    @classmethod
    def new_session(cls):
        return cls.__session()


def to_db_value(v) -> str:
    db_v = ','.join(v) if isinstance(v, list) else v
    escaped_v = db_v.replace("'", "''")
    return f"'{escaped_v}'"


def init_logging():
    logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO, stream=sys.stdout)

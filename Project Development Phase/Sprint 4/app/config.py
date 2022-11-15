from os import environ
from dotenv import load_dotenv
load_dotenv()


# FLASK
FLASK_HTTP_PORT         = environ.get("FLASK_HTTP_PORT")
SECRET_KEY              = environ.get("SECRET_KEY")


# IBM DB
DB2_PROTOCOL            = environ.get("DB2_PROTOCOL")
DB2_HOSTNAME            = environ.get("DB2_HOSTNAME")
DB2_PORT                = environ.get("DB2_PORT")
DB2_USER                = environ.get("DB2_USER")
DB2_PASSWORD            = environ.get("DB2_PASSWORD")
DB2_DATABASE            = environ.get("DB2_DATABASE")
DB2_POOL_CONNECTIONS    = environ.get("DB2_POOL_CONNECTIONS")


# MAIL
MAIL_API_KEY           = environ.get("SENDGRID_MAIL_API_KEY")
MAIL_DEFAULT_SENDER     = environ.get("MAIL_DEFAULT_SENDER")


# Type conversions
DB2_POOL_CONNECTIONS    = bool(DB2_POOL_CONNECTIONS) if DB2_POOL_CONNECTIONS else True

DB2_CONNECTION_STR = "DATABASE={};HOSTNAME={};PORT={};PROTOCOL={};UID={};PWD={};SECURITY=SSL;".format(
    DB2_DATABASE,
    DB2_HOSTNAME,
    DB2_PORT,
    DB2_PROTOCOL,
    DB2_USER,
    DB2_PASSWORD
)
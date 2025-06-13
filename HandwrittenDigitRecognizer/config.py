import urllib

class Config:
    DRIVER = "ODBC Driver 17 for SQL Server"
    SERVER = "DESKTOP-MLND08F\\SQLEXPRESS"
    DATABASE = "DigitRecognizerDB"

    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc://{server}/{db}?driver={driver}&trusted_connection=yes"
        .format(
            server=SERVER,
            db=DATABASE,
            driver=urllib.parse.quote_plus(DRIVER)
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'ivasla07@gmail.com'
    MAIL_PASSWORD = 'ptwptosgvkdulhlk'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
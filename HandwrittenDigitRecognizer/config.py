import urllib

class Config:
    DRIVER = "ODBC Driver 17 for SQL Server"
    SERVER = "DESKTOP-MLND08F\\SQLEXPRESS"
    DATABASE = "DigitRecognizerDB"

    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc://@{server}/{db}?driver={driver}&trusted_connection=yes"
        .format(
            server=SERVER,
            db=DATABASE,
            driver=urllib.parse.quote_plus(DRIVER)
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'
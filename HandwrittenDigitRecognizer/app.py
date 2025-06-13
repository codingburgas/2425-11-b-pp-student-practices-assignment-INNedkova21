from flask import Flask
from HandwrittenDigitRecognizer.ai import ai
from config import Config
from HandwrittenDigitRecognizer.extensions import db, login_manager
from HandwrittenDigitRecognizer.main.routes import main
from HandwrittenDigitRecognizer.auth import auth
from HandwrittenDigitRecognizer.models.user import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(ai)

    with app.app_context():
        db.create_all()

    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
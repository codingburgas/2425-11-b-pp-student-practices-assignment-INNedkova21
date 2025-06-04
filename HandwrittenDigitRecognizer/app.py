from flask import Flask
from config import Config
from extensions import db, login_manager
from main.routes import main
from auth import auth
from models.user import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

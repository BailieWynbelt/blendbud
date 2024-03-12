from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

mongo = PyMongo()
login_manager = LoginManager()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    mongo.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        from auth import auth_blueprint
        app.register_blueprint(auth_blueprint)

    return app

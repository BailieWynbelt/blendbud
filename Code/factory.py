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

    from auth import auth_blueprint, search_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(search_blueprint)

    return app

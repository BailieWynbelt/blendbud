from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_cors import CORS
mongo = PyMongo()
login_manager = LoginManager()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    CORS(app, supports_credentials=True)
    mongo.init_app(app)
    login_manager.init_app(app)
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False 
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True
    jwt = JWTManager(app)
    jwt.init_app(app)
    
    from auth import auth_blueprint, search_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(search_blueprint)

    return app

from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_jwt_extended import JWTManager


app = Flask(__name__)
app.config.from_object('config.Config')

mongo = PyMongo(app)
login_manager = LoginManager(app)
jwt = JWTManager(app)


from factory import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

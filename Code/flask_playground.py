from flask import Flask
from flask_pymongo import PyMongo
import bcrypt
from flask import request, jsonify
from flask_login import LoginManager, UserMixin, login_user

login_manager = LoginManager(app)

app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb+srv://servad:Ta527eZ3eqUWeA9s@tastebud.opgas9v.mongodb.net/TasteBud?retryWrites=true&w=majority'
mongo = PyMongo(app)


@app.route('/register', methods=['POST'])
def register():
    users = mongo.db.user  
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 400
    if users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user_id = users.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password
    }).inserted_id

    return jsonify({"message": "User registered successfully", "user_id": str(user_id)}), 201

@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.user
    username = request.form.get('username')
    password = request.form.get('password')

    user = users.find_one({"username": username})

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

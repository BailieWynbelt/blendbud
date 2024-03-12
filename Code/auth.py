from flask import Blueprint, request, jsonify
from flask_login import login_user
from flask_jwt_extended import create_access_token
from application import app, mongo, login_manager
from models import User
import bcrypt
from flask_jwt_extended import create_access_token
from bson.objectid import ObjectId
from flask_jwt_extended import jwt_required
auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/protected', methods=['GET'])
@jwt_required()
def protected_route():
    return jsonify({"message": "Access granted to protected route"}), 200

@login_manager.user_loader
def load_user(user_id):
    users = mongo.db.user
    return users.find_one({"_id": user_id})

@auth_blueprint.route('/register', methods=['POST'])
def register():
    users = mongo.db.user  
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 400
    if users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 406

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user_id = users.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password
    }).inserted_id

    return jsonify({"message": "User registered successfully", "user_id": str(user_id)}), 201

@auth_blueprint.route('/login', methods=['POST'])
def login():
    users = mongo.db.user
    username = request.form.get('username')
    password = request.form.get('password')

    user_data = users.find_one({"username": username})

    user = User(user_data) if user_data else None

    if user and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
        login_user(user) 
        access_token = create_access_token(identity=str(user.id))  
        return jsonify({"message": "Login successful", "access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


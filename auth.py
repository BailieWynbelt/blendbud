from flask import Blueprint, request, jsonify
from flask_login import login_user
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from factory import  mongo, login_manager
from models import User
import bcrypt
import datetime
from bson.objectid import ObjectId
from bson.json_util import dumps

auth_blueprint = Blueprint('auth', __name__)

search_blueprint = Blueprint('search', __name__)

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
    data = request.get_json()  
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

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
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user_data = users.find_one({"username": username})

    user = User(user_data) if user_data else None

    if user and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
        login_user(user) 
        access_token = create_access_token(identity=str(user.id))  
        return jsonify({"message": "Login successful", "access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401
    
@search_blueprint.route('/search', methods=['GET'])
def search():
    wines_collection = mongo.db.wines
    query = request.args.get('query')  
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    search_result = wines_collection.aggregate([
        {
            '$search': {
                'index': 'default', 
                'text': {
                    'query': query,
                    'path':  ['name', 'type', 'flavor_profile']
                }
            }
        },
        {
            '$limit': 20 
        }
    ])
    results = list(search_result)

    return jsonify(dumps(results)), 200


@auth_blueprint.route('/post_comment', methods=['POST'])
@jwt_required()
def post_comment():
    user_id = get_jwt_identity()
    db = mongo.db.comments
    data = request.get_json()
    wine_id = data.get('wine_id')
    comment_content = data.get('comment')
    star_rating = data.get('rating')
    
    if not wine_id or not comment_content or not star_rating:
        return jsonify({"error": "Missing data for posting a comment"}), 400

    comment = {
        'user_id': user_id,
        'wine_id': wine_id,
        'comment': comment_content,
        'rating': star_rating,
        'timestamp': datetime.datetime.now()
    }
    db.insert_one(comment)

    return jsonify({"message": "Comment posted successfully"}), 200
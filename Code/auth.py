from flask import Blueprint, request, jsonify
from flask_login import login_user
from flask_jwt_extended import  create_access_token, get_jwt_identity, jwt_required
from factory import  mongo, login_manager
from models import User
import bcrypt
import datetime
from bson.objectid import ObjectId
from bson.json_util import dumps
from flask import session

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
    email = data.get('email')
    password = data.get('password')

    user_data = users.find_one({"email": email})

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
    if 'recent_searches' not in session:
        session['recent_searches'] = []
    session['recent_searches'].append(query)
    session['recent_searches'] = session['recent_searches'][-10:]

    return jsonify(dumps(results)), 200

@search_blueprint.route('/search_user', methods=['GET'])
def search_user():
    query = request.args.get('query') 

    if not query:
        return jsonify({"error": "No search query provided"}), 400

    search_result = mongo.db.user.aggregate([
        {
            '$search': {
                'index': 'profile',  
                'text': {
                    'query': query,
                    'path': 'username'  
                }
            }
        },
        {
            '$limit': 20
        }
    ])

    users = list(search_result)
    user_list = [{'username': user['username'], 'id': str(user['_id'])} for user in users]

    return jsonify(user_list), 200


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

@search_blueprint.route('/wine/<wine_id>', methods=['GET'])
def get_wine_profile(wine_id):

    wine_data = mongo.db.wines.find_one({"_id": wine_id})

    if not wine_data:
        return jsonify({"error": "Wine not found"}), 404

    return jsonify(dumps(wine_data)), 200

@search_blueprint.route('/food/<food_id>', methods=['GET'])
def get_food_profile(food_id):

    food_data = mongo.db.foods.find_one({"_id": food_id})

    if not food_data:
        return jsonify({"error": "Food not found"}), 404

    return jsonify(dumps(food_data)), 200

@search_blueprint.route('/test', methods=['GET'])
def test_route():
    return jsonify({"message": "Test route works"}), 200

@auth_blueprint.route('/edit_profile', methods=['POST'])
@jwt_required()
def edit_profile():
    user_id = get_jwt_identity()  
    users = mongo.db.user 

    data = request.get_json()
    new_username = data.get('username')
    bio = data.get('bio')

    user = users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return jsonify({"error": "User not found"}), 404

    update_data = {}
    if new_username:
        update_data['username'] = new_username
    if bio is not None:  
        update_data['bio'] = bio

    if update_data:
        users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

    return jsonify({"message": "Profile updated successfully"}), 200


@auth_blueprint.route('/profile/<user_id>', methods=['GET'])
@jwt_required(optional=True)
def get_user_profile(user_id):
    user = mongo.db.user.find_one({"_id": ObjectId(user_id)}, {'username': 1, 'bio': 1, '_id': 0})

    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user), 200
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, make_response
from flask_login import login_user, login_required, current_user
from flask_jwt_extended import  create_access_token, get_jwt_identity, jwt_required
from factory import mongo, login_manager
from models import User
import bcrypt
import datetime
from bson.objectid import ObjectId
from bson.json_util import dumps
import logging
import suggest as suggest
import jwt

auth_blueprint = Blueprint('auth', __name__)

search_blueprint = Blueprint('search', __name__)


@auth_blueprint.route('/')
def index():
    return redirect(url_for('home'))

@auth_blueprint.route('/protected', methods=['GET'])
@jwt_required()
def protected_route():
    return jsonify({"message": "Access granted to protected route"}), 200
    
@search_blueprint.route('/description/<wine_id>')
def wine_description(wine_id):
    wine_data = mongo.db.wines.find_one({"_id": wine_id})
    food_ids = wine_data.get('food_ids')
    food_ids = [food.strip() for food in food_ids.split(';')]
    food_names = []
    if food_ids:
        print("food ids: ", food_ids)
        print("food id type: ", type(food_ids))
        food_ids = list(map(int, food_ids))
        foods = list(mongo.db.food.find({"_id": {"$in": food_ids}}))
        for food in foods:
            food_names.append(food["food_name"])
        
    print("food names: ", food_names)
    print("wine data: ", wine_data)
    if not wine_data:
        return jsonify({"error": "Wine not found"}), 404
    return render_template('description.html', wine=wine_data, food =food_names)
    
@login_manager.user_loader
def load_user(user_id):
    users = mongo.db.user
    return users.find_one({"_id": user_id})

@auth_blueprint.route('/signup')
def signup():
    return render_template('signup.html')

@auth_blueprint.route('/login')
def login_page():
    return render_template('login.html')

@auth_blueprint.route('/profile', methods=["GET"])
@jwt_required(optional=True)
def profile_page():
    print("Accessing profile page")
    current_user = get_jwt_identity()
    if not current_user:
        return render_template('login.html')
    users = mongo.db.user
    user_data = users.find_one({"_id": ObjectId(current_user)})

    if user_data:
        username = user_data.get('username')
        email = user_data.get('email')
        return render_template('profile.html', username = username, email = email)
    else:
        return jsonify({"error": "User not found"}), 404


@search_blueprint.route('/user_profile/<username>')
@jwt_required(optional=True)
def user_profile_page(username):
    current_userid = get_jwt_identity()
    users = mongo.db.user
    user_data = users.find_one({"username": username})
    if not current_userid:
        return render_template('user_profile.html', user=user_data)
    current_user = users.find_one({"_id": current_userid})
    if not user_data:
        return jsonify({"error": "Wine not found"}), 404
    return render_template('user_profile.html', user=user_data, current_user=current_user)

@auth_blueprint.route('/home')
@jwt_required(optional=True)
def home():
    print("Accessing home page")
    current_user = get_jwt_identity()
    if not current_user:
        return render_template('home.html')
    users = mongo.db.user
    user_data = users.find_one({'_id': ObjectId(current_user)})
    if user_data:
        return render_template('home.html', current_user=current_user)
    return render_template('home.html')

@auth_blueprint.route('/community')
@jwt_required(optional=True)
def community():
    print("Accessing the community page")
    current_user = get_jwt_identity()
    if not current_user:
        return render_template('community.html')
    users = mongo.db.user
    user_data = users.find_one({'_id': ObjectId(current_user)})
    if user_data:
        return render_template('community.html', current_user=current_user)
    return render_template('community.html')

@auth_blueprint.route('/search-page')
def show_search():
    return render_template('search.html')

@auth_blueprint.route('/community-search')
def show_community_search():
    return render_template('community_search.html')

@auth_blueprint.route('/about')
def about():
    return render_template('about.html')

@auth_blueprint.route('/intro_quiz', methods=["GET"])
@jwt_required(optional=False)
def intro_quiz():
    return render_template('intro_quiz.html')

@auth_blueprint.route('/quiz_submitted')
def submitted():
    return render_template('quiz_submitted.html')

'''
1. Register (/register)
Method: POST
URL: /auth/register
Description: Registers a new user with a username, email, and password.
Request Body:
{
  "username": "string",
  "email": "string",
  "password": "string"
}

+Success Response
Code 201
Content:
{
  "message": "User registered successfully",
  "user_id": "string"
}

-Error Response
Code 400
Content:
{
  "error": "Email already exists" 
  // Or "Username already exists", "Password is required"
}
'''
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


'''
2. Login (/login)
Method: POST
URL: /auth/login
Description: Authenticates a user and returns a JWT token.
Request Body:
{
  "email": "string",
  "password": "string"
}

+Success Response
Code 200
Content:
{
  "message": "Login successful",
  "access_token": "string"
}

-Error Response:
Code 401
Content:
{
  "error": "Invalid credentials"
}

'''
@auth_blueprint.route('/login', methods=['POST'])
def login():
    users = mongo.db.user
    email = request.form.get('email')
    password = request.form.get('password')

    user_data = users.find_one({"email": email})

    if not user_data or not bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
        logging.debug("Logging failure")
        return jsonify({"error": "Invalid credentials"}), 401
    access_token = create_access_token(identity=str(user_data['_id']))
    response = make_response(jsonify({"message": "Login successful"}))
    response.set_cookie('access_token_cookie', access_token)
    return response


'''
3. Search (/search)
Method: GET
URL: /search?query=string
Description: Searches for wines based on a query string.
Query Parameters:
query: string (required)
Success Response
Code: 200
Content example:
[{"_id": "1101213", "name": "Margaux", "type": "Margaux", "acidity": 4.1636753, "fizziness": null, "intensity": 3.8193736, 
"sweetness": 1.4682409, "tannin": 3.850287, "average_rating": 4.0, "price_amount": 52.16613404756387, "review_count": 11247.0, 
"food_ids": "4; 8; 11; 20", "flavor_profile": ["oak", "blackberry", "leather", "plum", "cherry"], "food_id": [4, 8, 11, 20]}, 
{"_id": "1287027", "name": "Margaux", "type": "Margaux", "acidity": 4.1794605, "fizziness": null, "intensity": 3.7525327, 
"sweetness": 1.5856922, "tannin": 3.6996198, "average_rating": 4.2, "price_amount": 32.603833779727424, "review_count": 14047.0, 
"food_ids": "4; 8; 11; 20", "flavor_profile": ["leather", "oak", "blackcurrant", "tobacco", "blackberry"], "food_id": [4, 8, 11, 20]}, ...]
Error Response:
Code: 400 (Bad Request)
Content:
{
  "error": "No search query provided"
}
'''
@search_blueprint.route('/search')
def search():
    query = request.args.get('query')
    
    if query:
        wines_collection = mongo.db.wines
        search_result = wines_collection.aggregate([
            {
                '$search': {
                    'index': 'default',
                    'text': {
                        'query': query,
                        'path': ['name', 'type', 'flavor_profile']
                    }
                }
            },
            {'$limit': 20}
        ])
        results = list(search_result)
        return jsonify(results)
    else:
        return render_template('search.html')



@search_blueprint.route('/search_user')
def search_user():
    query = request.args.get('query')
    print("query: ", query)
    if query:
        user_collection = mongo.db.user
        search_result = user_collection.aggregate([
            {
                '$search': {
                    'index': 'profile',
                    'text': {
                        'query': query,
                        'path': ['username', 'email']
                    }
                }
            },
            {'$limit': 20},
            {'$project': {'_id':0, 'username':1}}
        ])
        results = list(search_result)
        print("results:", results)
        return jsonify(results)
    else:
        return render_template('community_search.html')

'''
4. Post Comment (/post_comment)
Method: POST
URL: /auth/post_comment
Description: Posts a comment for a specific wine. Requires JWT authentication.
Request Body:
{
  "wine_id": "string",
  "comment": "string",
  "rating": integer
}

+Success Response
Code 200
Content:
{
  "message": "Comment posted successfully"
}

-Error Response:
Code 400
Content:
{
  "error": "Missing data for posting a comment"
}

'''

@auth_blueprint.route('/post_comment', methods=['POST'])
@jwt_required(optional=False)
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


'''
5. Wine Profile (/wine/<wine_id>)
Method: GET
URL: /wine/{wine_id}
Description: Retrieves the profile of a specific wine.
URL Parameters:
wine_id: string (required)
Success Response:
Code: 200
Content example: 
{"_id": "1171671", "name": "Margaux", "type": "Margaux", "acidity": 4.2452188, "fizziness": null, 
"intensity": 3.827806, "sweetness": 1.3505505, "tannin": 3.8045642, "average_rating": 4.0, "price_amount": 29.348839465189343, 
"review_count": 6295.0, "food_ids": "4; 8; 11; 20", "flavor_profile": ["oak", "leather", "plum", "blackberry", "earthy"], 
"food_id": [4, 8, 11, 20]}
Error Response:
Code: 404 (Not Found)
Content:
{
  "error": "Wine not found"
}

'''
@search_blueprint.route('/wine/<wine_id>', methods=['GET'])
def get_wine_profile(wine_id):

    wine_data = mongo.db.wines.find_one({"_id": wine_id})

    if not wine_data:
        return jsonify({"error": "Wine not found"}), 404

    return jsonify(dumps(wine_data)), 200

'''
6. Food Profile (/food/<food_id>)
Method: GET
URL: /food/{food_id}
Description: Retrieves the profile of a specific food.
URL Parameters:
food_id: string (required)
Success Response:
Code: 200
Content example:
{"_id": 4, "food_name": "Beef", "description": "Rich, full-bodied red wines like Cabernet Sauvignon or Malbec complement beef by 
balancing its robust flavors and high fat content with strong tannins and deep, complex flavors."}
Error Response:
Code: 404 (Not Found)
Content:
{
  "error": "Food not found"
}

'''
@search_blueprint.route('/food/<int:food_id>', methods=['GET'])
def get_food_profile(food_id):

    food_data = mongo.db.food.find_one({"_id": food_id})

    if not food_data:
        return jsonify({"error": "Food not found"}), 404

    return jsonify(dumps(food_data)), 200

@search_blueprint.route('/test', methods=['GET'])
def test_route():
    return jsonify({"message": "Test route works"}), 200

'''
7. Edit Profile (/edit_profile)
Method: POST
URL: /auth/edit_profile
Description: Edits the user's profile. Requires JWT authentication.
Request Body:
{
  "username": "string (optional)",
  "bio": "string (optional)"
}

+Success Response:
Code: 200
Content: 
{
  "Profile updated successfully"
}
-Error Response:
Code: 404 (Not Found)
Content:
{
  "error": "User not found"
}
-Code: 409 (Duplicate))
Content:
{
  "Username already exists"
}
'''
@auth_blueprint.route('/edit_profile', methods=['POST'])
@jwt_required(optional=False)
def edit_profile():
    user_id = get_jwt_identity()
    users = mongo.db.user

    data = request.get_json()
    new_username = data.get('username')
    bio = data.get('bio')

    if new_username and users.find_one({"username": new_username, "_id": {"$ne": ObjectId(user_id)}}):
        return jsonify({"error": "Username already exists"}), 409

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


'''
8. Profile
Method: GET
URL: /auth/profile/<username>
Description: Retrieves the profile of a user by their username. 
URL Parameters:
username: String
Headers:
Authorization (optional): A valid JWT if the request is being made by a logged-in user.

+Success Response:
Code: 200
Content: 
{
    "username": "johndoe",
    "bio": "bio of John Doe."
}

-Error Response:
Code: 404 (Not Found)
Content:
{
    "error": "User not found"
}

'''
@auth_blueprint.route('/profile/<username>', methods=['GET'])
@jwt_required(optional=True)
def get_user_profile(username):
    user = mongo.db.user.find_one({"username": username}, {'username': 1, 'bio': 1, '_id': 0, 'email':1})

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user), 200


'''
Pass back the token as a header if the function need it:
headers: 
{
    'Authorization': `Bearer ${accessToken}`
}
'''


'''
9. Preferences
Method: POST
URL: /auth/update_preferences
Description: Update/add preferences for chosen user 
Headers:
Authorization (required): A valid JWT
Request Body:
{
  "like_pref": "string list",
  "dis_pref": "string list"
}
Example:
{
  "like_pref": ["87702","56743"],
  "dis_pref": ["82341","257833"]
}
+Success Response:
Code: 200
Content: 
{
    "Preferences updated successfully",
    "user_id":
}
'''

@auth_blueprint.route('/update_preferences', methods=['POST'])
@jwt_required(optional=False)
def update_preferences():
    user_id = get_jwt_identity()
    data = request.get_json()
    like_pref = data.get('like_pref', [])
    dis_pref = data.get('dis_pref', [])



    pref_doc = mongo.db.preferences.find_one({"user_id": ObjectId(user_id)})

    if pref_doc:
        mongo.db.preferences.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": {"like_pref": like_pref, "dis_pref": dis_pref}}
        )
    else:
        mongo.db.preferences.insert_one({
            "user_id": ObjectId(user_id),
            "like_pref": like_pref,
            "dis_pref": dis_pref
        })

    return jsonify({"message": "Preferences updated successfully", "user_id": str(user_id)}), 200

'''
10. Add to Dislikes
URL: /auth/add_to_dislikes
Method: POST
URL: /auth/add_to_dislikes
Description: Adds a wine to the user's favorite list. Requires JWT authentication.
Request Body:
{
  "wine_id": "string"
}
'''
@auth_blueprint.route('/add_to_dislikes', methods=['POST'])
@jwt_required(optional=False)
def add_to_dislikes():
    user_id = get_jwt_identity()
    data = request.get_json()
    wine_id = data.get('wine_id')

    if not wine_id:
        return jsonify({"error": "Wine ID is required"}), 400

    pref_doc = mongo.db.preferences.find_one({"user_id": ObjectId(user_id)})

    if not pref_doc:
        mongo.db.preferences.insert_one({
            "user_id": ObjectId(user_id),
            "like_pref": [],
            "dis_pref": [wine_id],
            "flavor_pref": []
        })
        return jsonify({"message": "Added to dislikes"}), 200

    if wine_id not in pref_doc.get('dis_pref', []):
        mongo.db.preferences.update_one(
            {"user_id": ObjectId(user_id)},
            {"$addToSet": {"dis_pref": wine_id}}
        )
        return jsonify({"message": "Added to dislikes"}), 200
    else:
        return jsonify({"message": "Already in dislikes"}), 200


'''
10. Add to Favorites
URL: /auth/add_to_favorites
Method: POST
URL: /auth/add_to_favorites
Description: Adds a wine to the user's favorite list. Requires JWT authentication.
Request Body:
{
  "wine_id": "string"
}
'''
@auth_blueprint.route('/add_to_favorites', methods=['POST'])
@jwt_required(optional=False)
def add_to_favorites():
    user_id = get_jwt_identity()
    data = request.get_json()
    wine_id = data.get('wine_id')

    if not wine_id:
        return jsonify({"error": "Wine ID is required"}), 400

    pref_doc = mongo.db.preferences.find_one({"user_id": ObjectId(user_id)})

    if not pref_doc:
        mongo.db.preferences.insert_one({
            "user_id": ObjectId(user_id),
            "like_pref": [wine_id],
            "flavor_pref": []
        })
        return jsonify({"message": "Added to favorites"}), 200

    if wine_id not in pref_doc.get('like_pref', []):
        mongo.db.preferences.update_one(
            {"user_id": ObjectId(user_id)},
            {"$addToSet": {"like_pref": wine_id}}
        )
        return jsonify({"message": "Added to favorites"}), 200
    else:
        return jsonify({"message": "Already in favorites"}), 200

'''
10. Remove from Favorites
URL: /auth/remove_from_favorites
Method: POST
URL: /auth/remove_from_favorites
Description: Remove a wine from the user's favorite list. Requires JWT authentication.
Request Body:
{
  "wine_id": "string"
}
'''
@auth_blueprint.route('/remove_from_favorites', methods=['POST'])
@jwt_required(optional=False)
def remove_from_favorites():
    user_id = get_jwt_identity()
    data = request.get_json()
    wine_id = data.get('wine_id')

    if not wine_id:
        return jsonify({"error": "Wine ID is required"}), 400

    pref_doc = mongo.db.preferences.find_one({"user_id": ObjectId(user_id)})

    if not pref_doc:
        return jsonify({"error": "User preferences not found"}), 404

    if wine_id in pref_doc.get('like_pref', []):
        mongo.db.preferences.update_one(
            {"user_id": ObjectId(user_id)},
            {"$pull": {"like_pref": wine_id}}
        )
        return jsonify({"message": "Removed from favorites"}), 200
    else:
        return jsonify({"error": "Wine not in favorites"}), 400

'''
11. Check Favorite
Method: POST
URL: /auth/check_favorite
Description: Checks if a wine is in the user's favorite list. Requires JWT authentication.
Request Body:
{
  "wine_id": "string"
}
Content:
{"is_favorite": true} 
{"is_favorite": false} 
'''
@auth_blueprint.route('/check_favorite', methods=['POST'])
@jwt_required(optional=False)
def check_favorite():
    user_id = get_jwt_identity()
    data = request.get_json()
    wine_id = data.get('wine_id')
    
    if not wine_id:
        return jsonify({"error": "No wine ID provided"}), 400

    pref_doc = mongo.db.preferences.find_one({"user_id": ObjectId(user_id)})

    if not pref_doc:
        return jsonify({"is_favorite": False}), 200

    is_favorite = wine_id in pref_doc.get('like_pref', [])
    return jsonify({"is_favorite": is_favorite}), 200


'''
12. User Suggestions
Method: GET
URL: /auth/top_wines
Description: return the top 5 suggested wines for a user
Content:
5 top suggested wines for the user (requires authentication)
'''

@search_blueprint.route('/top_wines', methods=['GET'])
@jwt_required(optional=True)
def top_wines():
    user_id = get_jwt_identity()

    if not user_id:
        wines_collection = mongo.db.wines
        top_wines = wines_collection.find({},{"_id": 1}).sort("average_rating",-1).limit(5)
        top_wines_ids = [wine["_id"] for wine in top_wines]
        to_suggest = get_suggestion_names(top_wines_ids)
        return jsonify(dumps(to_suggest)), 200

    suggestions = []
    pref_doc = mongo.db.preferences.find_one({"user_id": ObjectId(user_id)})
    if not pref_doc:
        print('User has no preferences indicated')
        suggestions = suggest.suggest_wines("flavor", [])
        to_suggest = get_suggestion_names(suggestions)
        return jsonify(dumps(to_suggest)), 200
        
    like_pref = pref_doc.get('like_pref', [])
    flav_pref = pref_doc.get('flavor_pref').split(",")
    print("DO NOT RECOMMEND THESE ALREADY LIKED: ", like_pref)
    if len(like_pref) > 0:
        print("Suggesting based on liked wines")
        suggestions = suggest.suggest_wines("like", like_pref)
    elif len(like_pref) == 0:
        print("Suggesting based on liked flavors, or for empty user")
        suggestions = suggest.suggest_wines("flavor", flav_pref)
        print("suggestions??", suggestions)

    to_suggest = get_suggestion_names(suggestions)
    print("to suggest??", to_suggest)
    return jsonify(dumps(to_suggest)), 200      # returns a list of names and average_ratings rn

def get_suggestion_names(suggestions):
    suggestions_cursor = mongo.db.wines.find({'_id': {'$in': suggestions}}, {"_id": 1, "name": 1, "average_rating": 1})
    suggestions_list = list(suggestions_cursor)
    to_suggest = []
    for s in suggestions_list:
        print(s["name"])
        to_suggest.append({"id": s["_id"], "name": s["name"], "average_rating": s["average_rating"]})
    return to_suggest

'''
13. Blend Suggestions (2 Users)
Method: GET
URL: /auth/top_blends
Description: return the top 5 suggested blend wines for two users
Content:
5 top suggested blended wines for the two users (requires authentication)
'''

@auth_blueprint.route('/top_blends', methods=['POST'])
@jwt_required(optional=True)
def top_blends():
    user_id = get_jwt_identity()
    if not user_id:
        return "Must be logged in to blend with another user", 400
    username2 = request.form.get('username')
    user2 = mongo.db.user.find_one({"username": username2})
    user_id2 =user2['_id']
    pref_doc1 = mongo.db.preferences.find_one({"user_id": user_id})
    like_pref1 = pref_doc1.get('like_pref', []) if pref_doc1 else []
    flav_pref1 = pref_doc1.get('flavor_pref') if pref_doc1 else ''
    pref_doc2 = mongo.db.preferences.find_one({"user_id": user_id2})
    like_pref2 = pref_doc2.get('like_pref', []) if pref_doc2 else []
    flav_pref2 = pref_doc2.get('flavor_pref') if pref_doc2 else ''

    suggestions = suggest.suggest_wine_blend(like_pref1, flav_pref1, like_pref2, flav_pref2)
    to_suggest = get_suggestion_names(suggestions)

    return jsonify(dumps(to_suggest)), 200

'''
15.
Method: POST
URL: /auth/quiz
Description: submits quiz results to the preferences table in the data base
Content:
A list of liked flavors
'''
@auth_blueprint.route('/quiz', methods=['POST'])
@jwt_required()
def quiz():
    user_id = get_jwt_identity()
    preferences = mongo.db.preferences

    insert = request.form['checkboxvalue']

    check_user = preferences.find_one({"user_id": ObjectId(user_id)})

    if check_user:
        mongo.db.preferences.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": {"flavor_pref": insert}}
        )
    else:
        mongo.db.preferences.insert_one({
            "user_id": ObjectId(user_id),
            "flavor_pref": insert
        })

    return jsonify({"message": "Preferences updated successfully", "user_id": str(user_id)}), 200

'''
16.
Method: POST
URL: /auth/logout
Description: Removes access token from a user to logout
Content:
access token
'''
@auth_blueprint.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({"message": "Logout successful"}))
    response.set_cookie('access_token_cookie', '')
    return response

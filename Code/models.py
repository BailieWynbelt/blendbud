from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data.get("username")
        self.email = user_data.get("email")
        self.password = user_data.get("password")
        self.bio = user_data.get("bio")

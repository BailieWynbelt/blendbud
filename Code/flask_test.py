import unittest
from application import app, mongo
import bcrypt

class RegistrationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            mongo.db.user.delete_many({'username': 'testuser'})

    def test_registration_success(self):
        new_user = {
            'username': 'testuser',
            'email': 'test1@example.com',
            'password': 'testpassword1'
        }
        response = self.app.post('/register', data=new_user)
        self.assertEqual(response.status_code, 201)

    def test_duplicate_username(self):
        self.app.post('/register', data={'username': 'testuser2', 
                                         'email': 'test@example.com', 
                                         'password': 'testpassword'})
        duplicate_user = {
            'username': 'testuser2',
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        response = self.app.post('/register', data=duplicate_user)
        self.assertEqual(response.status_code, 400)

class LoginTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            mongo.db.user.delete_many({'username': 'testuser'})
            mongo.db.user.insert_one({'username': 'testuser', 'password': bcrypt.hashpw('testpassword'.encode('utf-8'), bcrypt.gensalt())})

    def test_login_success(self):
        valid_credentials = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.app.post('/login', data=valid_credentials)
        self.assertEqual(response.status_code, 200)

    def test_login_failure(self):
        invalid_credentials = {
            'username': 'wronguser',
            'password': 'wrongpassword'
        }
        response = self.app.post('/login', data=invalid_credentials)
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()

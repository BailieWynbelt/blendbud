import unittest
from factory import create_app, mongo


#python -m unittest flask_test.BaseTestCase
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            mongo.db.user.delete_many({'username': 'testuser'})
            mongo.db.user.delete_many({'username': 'guestuser'})
            mongo.db.user.delete_many({'email': 'test1@example.com'})
            mongo.db.comments.delete_many({'user_id': '65fd9ca88d7213ffc0cf43f9'})


#python -m unittest flask_test.RegistrationTestCase
class RegistrationTestCase(BaseTestCase):
    def test_registration_success(self):
        new_user = {
            'username': 'testuser',
            'email': 'test1@example.com',
            'password': 'testpassword1'
        }
        response = self.client.post('/auth/register', json=new_user)
        self.assertEqual(response.status_code, 201)

    def test_duplicate_username(self):
        first_user = {'username': 'testuser2', 'email': 'test@example.com', 'password': 'testpassword'}
        self.client.post('/auth/register', json=first_user)
        duplicate_user = {
            'username': 'testuser2',
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        response = self.client.post('/auth/register', json=duplicate_user)
        self.assertEqual(response.status_code, 400)


#python -m unittest flask_test.LoginTestCase
class LoginTestCase(BaseTestCase):
    def test_login_success(self):
        valid_credentials = {
            'email': 'test1@example.com',
            'password': 'testpassword1'
        }
        self.client.post('/auth/register', json=valid_credentials)
        response = self.client.post('/auth/login', json=valid_credentials)
        self.assertEqual(response.status_code, 200)

    def test_login_failure(self):
        invalid_credentials = {
            'email': 'wronguser',
            'password': 'wrongpassword'
        }
        response = self.client.post('/auth/login', json=invalid_credentials)
        self.assertEqual(response.status_code, 401)


#python -m unittest flask_test.SearchTestCase
class SearchTestCase(BaseTestCase):
    def test_search(self):
        response = self.client.get('/search?query=Margaux')
        self.assertEqual(response.status_code, 200)
        print(response.get_json()) 


#python -m unittest flask_test.NameSearchTestCase
class NameSearchTestCase(BaseTestCase):
    def test_name_search(self):
        response = self.client.get('/search?query=Lilia')
        self.assertEqual(response.status_code, 200)
        print(response.get_json()) 

#python -m unittest flask_test.CommentPostTestCase
class CommentPostTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.token = self.login_and_get_token()

    def login_and_get_token(self):
        login_credentials = {
            'email': 'test1@example.com',
            'password': 'testpassword1'
        }
        self.client.post('/auth/register', json=login_credentials)
        response = self.client.post('/auth/login', json=login_credentials)
        return response.get_json()['access_token']

    def test_post_comment_success(self):
        comment_data = {
            'wine_id': '1171671', 
            'comment': 'Great wine!',
            'rating': 5
        }
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = self.client.post('/auth/post_comment', json=comment_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Comment posted successfully', response.get_json()['message'])

    def test_post_comment_missing_data(self):
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = self.client.post('/auth/post_comment', json={'comment': 'Missing wine_id and rating'}, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing data for posting a comment', response.get_json()['error'])

#python -m unittest flask_test.EditProfileTestCase
class EditProfileTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.token = self.login_and_get_token()

    def login_and_get_token(self):
        login_credentials = {
            'email': 'liliasteele@gmail.com',
            'password': 'supersecretpassword'
        }
        response = self.client.post('/auth/login', json=login_credentials)
        return response.get_json()['access_token']
    
    def test_edit_profile_success(self):
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        new_profile_data = {
            'username': 'Lilac Steele',
            'bio': 'I love Lilac'
        }
        response = self.client.post('/auth/edit_profile', json=new_profile_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Profile updated successfully', response.get_json()['message'])



# python -m unittest flask_test.WineProfileTestCase
class WineProfileTestCase(BaseTestCase):
    def test_wine_profile_success(self):
        wine_id = '1171671'  
        response = self.client.get(f'/wine/{wine_id}')
        self.assertEqual(response.status_code, 200)
        wine_data = response.get_json()
        print(wine_data)  

    def test_wine_profile_not_found(self):
        wine_id = '507f1f77bcf86cd799439999'  
        response = self.client.get(f'/wine/{wine_id}')
        self.assertEqual(response.status_code, 404)

# python -m unittest flask_test.FoodProfileTestCase
class FoodProfileTestCase(BaseTestCase):
    def test_food_profile_success(self):
        food_id = 4 
        response = self.client.get(f'/food/{food_id}')
        self.assertEqual(response.status_code, 200)
        food_data = response.get_json()
        print(food_data) 

    def test_food_profile_not_found(self):
        food_id = '507f1f77bcf86cd799439999'  
        response = self.client.get(f'/food/{food_id}')
        self.assertEqual(response.status_code, 404)

# python -m unittest flask_test.RouteTestCase
class RouteTestCase(BaseTestCase):
    def test_test_route(self):
        response = self.client.get('/test') 
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data, {"message": "Test route works"})

# python -m unittest flask_test.ProfileTestCase
class ProfileTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.token = self.register_and_login()

    def register_and_login(self):
        user_data = {
            'email': 'liliasteele@gmail.com',
            'password': 'supersecretpassword'
        }
        login_response = self.client.post('/auth/login', json=user_data)
        return login_response.get_json()['access_token']

    def test_owner_viewing_own_profile(self):
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = self.client.get('/auth/profile', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Lilac Steele', response.get_json()['username'])
    






if __name__ == '__main__':
    unittest.main()

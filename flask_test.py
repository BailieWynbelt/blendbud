import unittest
from factory import create_app, mongo

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            mongo.db.user.delete_many({'username': 'testuser'})
            mongo.db.comments.delete_many({'user_id': '65fd9ca88d7213ffc0cf43f9'})

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


class LoginTestCase(BaseTestCase):
    def test_login_success(self):
        valid_credentials = {
            'username': 'testuser',
            'password': 'testpassword1'
        }
        self.client.post('/auth/register', json=valid_credentials)
        response = self.client.post('/auth/login', json=valid_credentials)
        self.assertEqual(response.status_code, 200)

    def test_login_failure(self):
        invalid_credentials = {
            'username': 'wronguser',
            'password': 'wrongpassword'
        }
        response = self.client.post('/auth/login', json=invalid_credentials)
        self.assertEqual(response.status_code, 401)


class SearchTestCase(BaseTestCase):
    def test_search(self):
        response = self.client.get('/search?query=Margaux')
        self.assertEqual(response.status_code, 200)
        print(response.get_json()) 

class CommentPostTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.token = self.login_and_get_token()

    def login_and_get_token(self):
        login_credentials = {
            'username': 'testuser',
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

if __name__ == '__main__':
    unittest.main()

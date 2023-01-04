"""View tests."""

import os
from unittest import TestCase
from flask import session
from models import db, connect_db, User, Recipe, Favorites
from forms import UserAddForm, UserLoginForm, UserEditForm

os.environ['DATABASE_URL'] = "postgresql:///food-test"

from app import app, CURR_USER_KEY, do_login, do_logout

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING']=True
app.config['DEBUG_TB_HOST'] = ["don't-show-debug-toolbar"]
app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.register(username="testuser",
                                    email="test@test.com",
                                    password="testuser")
        
        self.testuser_id = 300
        self.testuser.id = self.testuser_id

        db.session.commit()
    
    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_register_get(self):
        """Test_register_get_route"""

        with app.test_client() as client:
            resp = client.get("/register")
           
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join us today', str(resp.data))
            
    def test_register_post(self):
        """Test_signup_post_route"""

        with app.test_client() as client:
            resp = client.post("/register", json={
                "username":"testuser2",
                "email": "test2@test.com",
                "password": "testuser2"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", str(resp.data))
    
    def test_signin_get(self):
        """Test_signin_get_route"""

        with app.test_client() as client:
            resp = client.get("/signin")
           
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome back', str(resp.data))
    
    def test_signin_post(self):
        """Test_signin_post_route"""

        with app.test_client() as client:
            resp = client.post("/signin", json={
                "username":"testuser2",
                "password":"testuser2"}, follow_redirects=True)
           
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser2', str(resp.data))
    
    def test_fail_signin(self):
        """Wrong credentials"""

        with app.test_client() as client:
            resp = client.post("/signin", json={
                "username":"testuser_wrong",
                "password":"testuser_wrong"}, follow_redirects=True)
            
            self.assertIn('Invalid credentials', str(resp.data))
    
    def test_logout(self):
        """Test logout route"""

        with app.test_client() as client:
            resp = client.get('/logout', json={
                "username":"testuser",
                "password":"testuser"},
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Register', str(resp.data))
    
    def test_user_homepage(self):
        """Test user homepage"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                #make sure user is logged in
                sess[CURR_USER_KEY] = self.testuser_id
                
            resp = client.get(f'/users/{self.testuser_id}')

            self.assertIn('My Info', str(resp.data))
            self.assertEqual(sess[CURR_USER_KEY], 300)
            self.assertIn('testuser', str(resp.data))
    
    def test_navigation_no_user(self):
        """Test navigation"""
        with app.test_client() as client:
            resp = client.post('/recipes', data={
                "next":"Next >>>"
            }, follow_redirects=True)
            
            self.assertEqual(session['offset'], 8)
            self.assertIn('Recipes of the day', str(resp.data))


    def test_navigation_user(self):
        """Test User's recipes navigation"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                #make sure user is logged in
                sess[CURR_USER_KEY] = self.testuser_id
            resp = client.post(f'/{self.testuser_id}/recipes', data={
                "res_next":"Next >>>"
            }, follow_redirects=True)

            self.assertEqual(session['index'], 4)
            self.assertIn('My Info', str(resp.data))

    
    def test_add_to_fav(self):
        """Test add to users favs"""
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                #make sure user is logged in
                sess[CURR_USER_KEY] = self.testuser_id
            resp = client.post(f'/users/{self.testuser_id}', data={
                "rec_to_save":"646512"
            }, follow_redirects=True)
            saved_recipe = Recipe.query.get(646512)
            user = User.query.get(self.testuser_id)

            # the recipe exists in Recipe table
            self.assertIsNot(saved_recipe, None)
            # the recipe is added to user favorites
            self.assertIn(saved_recipe, user.favorites)


    def test_delete_from_fav(self):
        """Test delete form favs"""
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                #make sure user is logged in
                sess[CURR_USER_KEY] = self.testuser_id
            
            new_favorite = Favorites(recipe_id = 646512, user_id = self.testuser_id)

            resp = client.post(f'/users/{self.testuser_id}/favorites', data={
                "rec_to_delete":"646512"
            }, follow_redirects=True)
            removed_from_favs = Recipe.query.get(646512)
            user = User.query.get(self.testuser_id)

            # the recipe is deleted from to user favorites
            self.assertNotIn(removed_from_favs, user.favorites)

    def test_recipe_details(self):
        """Test recipes details view"""
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                #make sure user is logged in
                sess[CURR_USER_KEY] = self.testuser_id
            resp = client.get('/recipes/646512')
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Salmon Caesar Salad', str(resp.data))

    def test_user_settings_get(self):
        """Test user settings page"""
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                #make sure user is logged in
                sess[CURR_USER_KEY] = self.testuser_id
            resp = client.get(f'/users/{self.testuser_id}/update')
            user = User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(user.username, str(resp.data))
            self.assertIn('save-preferences', str(resp.data))

    def test_user_settings_post(self):
        """Test change settings route"""
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                #make sure user is logged in
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = client.post(f'/users/{self.testuser_id}/update', data={
                    "username":"testuser",
                    "email":"hnlkh@gmail.com",
                    "image_url":"",
                    "diet":"Vegan",
                    "intolerances":"Sesame",
                    "cuisine":"American",
                    "excludeIngredients":"egg, cheese"
            }, follow_redirects=True)
            
            user = User.query.get(self.testuser_id)
            
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(user.diet, "{Vegan}")
            self.assertEqual(user.intolerances, "{Sesame}")
            self.assertEqual(user.excludeIngredients, "egg, cheese")
            self.assertIn("<li>egg</li>", str(resp.data))
            
            

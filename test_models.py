import os
from unittest import TestCase
from models import db, User, Recipe, Favorites

os.environ['DATABASE_URL'] = "postgresql:///food-test"
from app import app

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        test_user1 = User(
            username="user1",
            email="user1@test.com",
            password="password1"
        )

        test_user2 = User(
            username="user2",
            email="user2@test.com",
            password="password2"
        )

        test_user3 = User(
            username="user3",
            email="user3@test.com",
            password="password3"
        )

        db.session.add(test_user1)
        db.session.add(test_user2)
        db.session.add(test_user3)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_user_table(self):
        """Check all added users"""
        users = User.query.all()

        # 3 users in users table
        self.assertEqual(len(users), 3)

    def test_user_model(self):
        """New user created"""

        u = User(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        
        # user added to db
        self.assertIn(u, User.query.all())
        # new user has 0 favorites
        self.assertEqual(len(u.favorites), 0)
    
    def test_fail_register(self):
        """Username/email is already used"""

        new_user = User(
            username="user1",
            email="something@gnmail.com",
            password="HASHED_PASSWORD"
        )
        try:
           db.session.add(new_user)
           db.session.commit()
        except:
           db.session.rollback()
           
        users = User.query.all()

        # user can not be added to db
        self.assertNotIn(new_user, users)
    
    def test_fail_register_missed_field(self):
        """Fail to create a new user with a missing notnullable field"""
        
        new_user = User(
            username="testuser",
            password="HASHED_PASSWORD"
        )

        try:
           db.session.add(new_user)
           db.session.commit()
        except:
           db.session.rollback()
           
        users = User.query.all()

        # user can not be created
        self.assertNotIn(new_user, users)
    
    def test_authenticate_user(self):
        """Authenticate registered user"""
        
        new_user = User.register("new_user1", "new_user1@gmail.com", "newpassword1")
        registered_user = User.authenticate("new_user1", "newpassword1")
        
        # user is authenticated
        self.assertEqual(new_user, registered_user)

    def test_fail_authenticate_user(self):
        """Fail to autenticate user(wrong credentials)"""

        new_user = User.register("new_user1", "new_user1@gmail.com", "newpassword1")
        registered_user = User.authenticate("wrong_name", "newpassword1")
        
        # could not authenticate user
        self.assertNotEqual(new_user, registered_user)

        
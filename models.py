from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect this database to provided Flask app."""

    db.app = app
    db.init_app(app)

class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
        index=True
    )

    password = db.Column(
            db.Text,
            nullable=False,
        )

    image_url = db.Column(
        db.Text,
        default="/static/user.png",
    )

    diet = db.Column(
        db.Text
    )

    intolerances = db.Column(
        db.Text
    )

    cuisine = db.Column(
        db.Text
    )

    excludeIngredients = db.Column(
        db.Text
    )

    favorites = db.relationship('Recipe', 
                                secondary='favorites',
                                backref='user')
    
    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def register(cls, username, email, password):
        """Sign up user. Hashes password and adds user to system."""

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        user = User(
            username=username,
            email=email,
            password=hashed_pwd
        )
        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.
        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.
        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()
        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
        return False

class Recipe(db.Model):
    """Recipes"""

    __tablename__='recipes'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    title = db.Column(
        db.Text, 
        nullable = False
    )

    image = db.Column(
        db.Text
    )

    def __repr__(self):
        return f"<Recipe #{self.id}: {self.title}>"

class Favorites(db.Model):

    __tablename__='favorites'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    recipe_id = db.Column(
                db.Integer, 
                db.ForeignKey('recipes.id')
    )

    user_id = db.Column(
                db.Integer,
                db.ForeignKey('users.id')
   )
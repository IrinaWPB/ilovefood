import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
import requests
from key import api_key
from forms import UserAddForm, UserLoginForm, UserEditForm
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Recipe, Favorites

CURR_USER_KEY = "curr_user"
offset = 0

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///meals'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "123")
toolbar = DebugToolbarExtension(app)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id
    # print(session.get('offset'))
    # offset = session.get('offset', 0)
    # print(offset)

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        # print(session['offset'])
        # session['offset'] = session['offset'] + 4
        # print(session['offset'])
        del session[CURR_USER_KEY]


def get_recipes(n, params='', offset=''):
    res = requests.get(f'https://api.spoonacular.com/recipes/complexSearch?apiKey={api_key}&number={n}{params}{offset}')
    j_recipes = res.json()
    return j_recipes['results']

def get_recipe(id):
    res = requests.get(f'https://api.spoonacular.com/recipes/{id}/information?apiKey={api_key}')
    j_recipe = res.json()
    return j_recipe

def convert_to_list(str):
    lst = str.replace('{', '').replace('}', '').replace('"', '').split(',')
    return lst

def get_query_string(user):
    query = ''
    # ingredients to exclude
    if user.excludeIngredients:
        exclude = user.excludeIngredients.replace(' ', '')
        query = f'&excludeIngredients={exclude}' 
    
    user_dict = user.__dict__
    for key,value in user_dict.items():
        if value and key in ['intolerances', 'cuisine', 'diet']:
            for val in convert_to_list(value):
                if val:
                    query += f'&{key}={val}' 
    return query
    

@app.route('/')
def homepage():
    """Welcome page"""

    if session.get('random_recipes'):
        recipes = session['random_recipes']
        offset_str = f'&offset={offset +12}'
    else:
        session['offset'] = offset + 12 
        recipes = get_recipes(8, offset)
        session['random_recipes'] = recipes
    print(offset, offset_str, session['offset'])      
     
    return render_template('homepage.html', recipes = recipes)



@app.route('/register', methods=["GET", "POST"])
def signup():
    """Handle user signup. Create new user and add to DB. 
    Redirect to user profile page. If the there already is a user with that username: 
    flash messageand re-present form."""

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
            )
            db.session.commit()

        except IntegrityError:
            flash('Username/email already taken', 'danger')
            return render_template('users/register.html', form=form)

        do_login(user)
        return redirect(f'users/{user.id}')

    else:
        return render_template('users/register.html', form=form)
    
@app.route('/signin', methods=["GET", "POST"])
def signin():
    """Handle user login."""

    form = UserLoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            return redirect(f'/users/{user.id}')

        flash("Invalid credentials.", 'danger')

    return render_template('users/signin.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    
    do_logout()
    return redirect('/')

@app.route('/users/<int:user_id>', methods=["POST", "GET"])
def user_homepage(user_id):
    """Show user's homepage with 5 random recipes of the day"""
    
    if not g.user or g.user.id != user_id:
        flash("Access denied", "danger")
        return redirect('/')

    
    user = User.query.get_or_404(user_id)
    

    if request.method == "POST":
        clicked_recipe_id = request.form['rec_to_save']

        if not Recipe.query.get(clicked_recipe_id):
            fav_recipe = get_recipe(clicked_recipe_id)
            recipe = Recipe(id = fav_recipe['id'],
                            title = fav_recipe['title'],
                            image = fav_recipe['image']
                            )
            db.session.add(recipe) 
            db.session.commit() 

        favorite = Favorites(recipe_id = clicked_recipe_id,
                            user_id = user_id)
        db.session.add(favorite)
        db.session.commit()
            
        return redirect(f'/users/{user_id}')


    prefs = {}
    user_dict = user.__dict__
    for key,value in user_dict.items():
        if value and key in ['intolerances', 'cuisine', 'diet']:
            #build formatted preference  dictionary
            prefs[key] = []
            for val in convert_to_list(value):
                if val != '':
                    prefs[key].append(val)   

    # offset = session['offset']
    # query = f'{query}&offset={offset}'
    # check if the page was already visited, if not - load 4 new recipes
    if session.get('recipes'):
        recipes = session['recipes']
       
    else:
        recipes = get_recipes(4, get_query_string(user))
        session['recipes'] = recipes
    
    
    # if user adds data to "by ingerdient" search form, add data to the main request query
    user_search_ing = request.args.get('search_by_ingredients')
    if user_search_ing:
        user_search_ing = user_search_ing.replace(' ', '')
        query = f'{get_query_string(user)}&includeIngredients={user_search_ing}'
        
    # add data (if submitted) from "by dish" search form
    user_search_dish = request.args.get('search_by_dish')
    if user_search_dish:
        query = f'{get_query_string(user)}&titleMatch={user_search_dish}'

    # add data (if submitted) from "by calories" search form
    user_search_calories = request.args.get('search_by_calories')
    if user_search_calories:
        query = f'{get_query_string(user)}&maxCalories={user_search_calories}'

    # checks if user used a search form
    if user_search_dish or user_search_calories or user_search_ing:
        
        recipes = get_recipes(4, query)
        session['recipes'] = recipes

    
    # create list of favorite ids to check if recipe needs an "add to favs" option 
    favs = []
    for fav in user.favorites:
        favs.append(fav.id)

    return render_template('users/user_homepage.html', 
                            user=user,
                            prefs = prefs, 
                            recipes = recipes,
                            favs = favs)
                           

@app.route('/users/<int:user_id>/favorites', methods=["POST", "GET"])
def show_favorite_recipes(user_id):
    """Show users favorite recipes"""
    
    if not g.user or g.user.id != user_id :
        flash("Access denied", "danger")
        return redirect('/')

    user = User.query.get_or_404(user_id)
    recipes = user.favorites

    if request.method == "POST":
        Favorites.query.filter_by(recipe_id = request.form['rec_to_delete']).delete()
        db.session.commit()
        return redirect(f'/users/{user_id}/favorites')

    return render_template('users/user_favorites.html', user = user, recipes = recipes)

@app.route('/users/<int:user_id>/update', methods = ["POST", "GET"])
def user_settings(user_id):
    """User settings page"""

    if not g.user or g.user.id != user_id:
        flash("Access denied", "danger")
        return redirect('/')

    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj = user)
    
    if form.validate_on_submit():
        
        user.username=form.username.data
        user.email=form.email.data
        user.image_url=form.image_url.data
        user.diet=form.diet.data
        user.intolerances=form.intolerances.data
        user.cuisine=form.cuisine.data
        user.excludeIngredients=form.excludeIngredients.data
        db.session.commit()
        session['recipes'] = get_recipes(4, get_query_string(user))
        return redirect(f'/users/{user_id}')

    return render_template('users/user_settings.html', user = user, form = form)

@app.route('/recipes/<int:recipe_id>')
def show_recipe_details(recipe_id):
    """Show recipe details"""

    if not g.user:
        flash("Please register", 'danger')
        return redirect('/register')

    recipe = get_recipe(recipe_id)

    return render_template("recipes/recipe.html", recipe = recipe)
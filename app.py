import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
import requests
from key import api_key
from forms import UserAddForm, UserLoginForm, UserEditForm
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Recipe, Favorites


CURR_USER_KEY = "curr_user"

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

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
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


@app.route('/', methods=["POST", "GET"])
def homepage():
    """Welcome page"""
    offset = session.get('offset',0)

# --------- Navigation buttons clicked---------
    if request.method == "POST":
        if request.form.get('next') == 'Next >>>':
            offset = offset + 8
        
        elif request.form.get('back') == '<<< Back':
            
            if offset >= 8:
                offset = offset - 8
            else:
                offset = 0
            
        session['offset'] = offset
        session['random_recipes'] = []
        return redirect('/')
   
    if not session.get('random_recipes'):
        print(offset)
        recipes = get_recipes(8,'',f'&offset={offset}')
        print(offset)
        session['random_recipes'] = recipes
       
    recipes_to_show = session['random_recipes']

    return render_template('homepage.html', recipes = recipes_to_show)

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
        
        session['query'] = ''
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
    session['recipes'] = []
    return redirect('/')

@app.route('/users/<int:user_id>', methods=["POST", "GET"])
def user_homepage(user_id):
    """Show user's homepage with 5 random recipes of the day"""
    
    if not g.user or g.user.id != user_id:
        flash("Access denied", "danger")
        return redirect('/')

    user = User.query.get_or_404(user_id)
    index = session.get('index', 0)

    if request.method == "POST":
        clicked_recipe_id = request.form.get('rec_to_save')

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
        return redirect(f'/users/{user.id}')

#----------------get route-----------

    # get formatted preference dictionary
    prefs = {}
    user_dict = user.__dict__
    for key,value in user_dict.items():
        if value and key in ['intolerances', 'cuisine', 'diet']:
            #build formatted preference  dictionary
            prefs[key] = []
            for val in convert_to_list(value):
                if val != '':
                    prefs[key].append(val)   
    
    query = session['query']

    # if user adds data to "by ingerdient" search form, add data to the main request query
    if request.args.get('search_by_ingredients') or request.args.get('search_by_dish') or request.args.get('search_by_calories'):
        session['query'] = ''
        session['index'] = 0
        if request.args.get('search_by_ingredients'):
            ing = request.args.get('search_by_ingredients').replace(' ', '')
            query = f'{get_query_string(user)}&includeIngredients={ing}'
            
        if request.args.get('search_by_dish'):
            dish = request.args.get('search_by_dish')
            query = f'{get_query_string(user)}&query={dish}'

        if request.args.get('search_by_calories'):
            cal = request.args.get('search_by_calories')
            query = f'{get_query_string(user)}&maxCalories={cal}'
        session['query'] = query
    
    recipe_list = get_recipes(100,query)
    print(f'Current query {query}')
    recipes_to_show = recipe_list[index:index+4]
    
    # create list of favorite ids to check if recipe needs an "add to favs" option 
    favs = []
    for fav in user.favorites:
        favs.append(fav.id)

    return render_template('users/user_homepage.html', 
                            user=user,
                            prefs = prefs, 
                            recipes = recipes_to_show,
                            favs = favs)
                           
@app.route('/<int:user_id>/recipes', methods=["POST"])
def navigation(user_id):
    index = session.get('index', 0)
    if request.form.get('res_next') == 'Next >>>':
        index = index + 4 
    elif request.form.get('res_back') == '<<< Back':
        if index >= 4:
            index = index - 4
        else:
            index = 0
    session['index'] = index
    return redirect(f'/users/{user_id}')

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
        
        recipes_list = get_recipes(f'&number=100', get_query_string(user))
        print(len(recipes_list))
        recipes_to_show = recipes_list[0:4]
        session['recipes'] = recipes_to_show
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
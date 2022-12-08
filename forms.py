from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SelectMultipleField, widgets
from wtforms.validators import InputRequired, Email, Length

DIETS = ['Gluten Free', 'Ketogenic', 'Vegetarian', 'Lacto-Vegetarian', 'Ovo-Vegetarian', 'Vegan', 'Pescetarian', 'Paleo', 'Primal', 'Low FODMAP', 'Whole30']
CUISINES = ['American', 'Caribbean', 'Chinese', 'Eastern European', 'French','Greek', 'Indian', 'Italian', 'Japanese', 'Korean','Latin American', 'Mediterranean',
            'Mexican', 'Middle Eastern', 'Nordic', 'Southern','Spanish', 'Thai', 'Vietnamese']
ALLERGIES = ['Dairy', 'Egg', 'Gluten', 'Grain', 'Peanut', 'Treenut', 'Seafood', 'Shellfish', 'Sesame', 'Soy', 'Sulfite', 'Wheat']


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[InputRequired()])
    email = StringField('E-mail', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])

class UserLoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])

class UserEditForm(FlaskForm):
    """Form to update user info"""

    username = StringField('Username', validators=[InputRequired()])
    email = StringField('E-mail', validators=[InputRequired(), Email()])
    image_url = StringField('Image URL')
    diet = MultiCheckboxField('Diets', choices=[(d,d) for d in DIETS]) 
    intolerances = MultiCheckboxField('Allergies', choices=[(al, al) for al in ALLERGIES])
    cuisine = MultiCheckboxField('Cuisine', choices=[(c, c) for c in CUISINES]) 
    excludeIngredients = StringField('Products to exclude:')
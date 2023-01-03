import requests
from key import api_key

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
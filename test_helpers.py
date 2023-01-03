import os
from unittest import TestCase
from helper import get_recipes, get_recipe, convert_to_list

class HelperTestCase(TestCase):
    """Test views for users."""

    def test_get_recipes(self):
        """Test getting recipes"""
        
        recipes = get_recipes(2)
        # request 2 recipes, get 2 recipes
        self.assertEqual(len(list(recipes)), 2)
        
    def test_get_recipe(self):
        """Test getting recipe details"""

        recipe = get_recipe(716429)
        
        # Check if keys are in recipe keys
        self.assertIn('diets', recipe.keys())
        self.assertIn('cuisines', recipe.keys())
        self.assertIn('healthScore', recipe.keys())
    
    def test_query_match(self):
        """Test is result matches query"""

        query = '&query=pasta&diet=vegan'
        recipes = get_recipes(2, query)
        
        recipe1 = get_recipe(recipes[0]['id'])
        recipe2 = get_recipe(recipes[1]['id'])
        
        # check if recipe 1 is vegan pasta
        self.assertIs(recipe1['vegan'], True)
        self.assertIn('Pasta', recipe1['title'])

        # check if recipe 2 is vegan pasta
        self.assertIs(recipe2['vegan'], True)
        self.assertIn('Pasta', recipe2['title'])

    def test_convert_to_list(self):
        """Test formatting user's input"""

        self.assertEqual(convert_to_list('{"eggs","butter","milk"}'), ['eggs', 'butter', 'milk'])



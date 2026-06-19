from flask import Flask, render_template, request, jsonify
import json
import re
from difflib import get_close_matches

app = Flask(__name__)

# Load recipes from JSON file
def load_recipes():
    try:
        with open('recipes.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default recipes if file doesn't exist
        return get_default_recipes()

def get_default_recipes():
    return [
        {
            "id": 1,
            "name": "Spaghetti Carbonara",
            "ingredients": ["pasta", "eggs", "parmesan", "bacon", "black pepper"],
            "instructions": "1. Cook pasta. 2. Fry bacon. 3. Mix eggs with parmesan. 4. Combine everything.",
            "prep_time": "20 minutes",
            "difficulty": "Medium"
        },
        {
            "id": 2,
            "name": "Chicken Stir Fry",
            "ingredients": ["chicken", "soy sauce", "vegetables", "garlic", "ginger", "oil"],
            "instructions": "1. Cook chicken. 2. Add vegetables. 3. Add sauce. 4. Stir fry until done.",
            "prep_time": "25 minutes",
            "difficulty": "Easy"
        },
        {
            "id": 3,
            "name": "Vegetable Soup",
            "ingredients": ["carrots", "celery", "onions", "tomatoes", "vegetable broth", "garlic"],
            "instructions": "1. Chop vegetables. 2. Sauté onions and garlic. 3. Add broth and vegetables. 4. Simmer.",
            "prep_time": "40 minutes",
            "difficulty": "Easy"
        },
        {
            "id": 4,
            "name": "Pancakes",
            "ingredients": ["flour", "milk", "eggs", "sugar", "baking powder", "butter"],
            "instructions": "1. Mix dry ingredients. 2. Add wet ingredients. 3. Cook on griddle.",
            "prep_time": "15 minutes",
            "difficulty": "Easy"
        },
        {
            "id": 5,
            "name": "Caesar Salad",
            "ingredients": ["lettuce", "parmesan", "croutons", "garlic", "olive oil", "eggs"],
            "instructions": "1. Wash lettuce. 2. Make dressing. 3. Toss everything together.",
            "prep_time": "15 minutes",
            "difficulty": "Easy"
        },
        {
            "id": 6,
            "name": "Beef Tacos",
            "ingredients": ["beef", "tortillas", "cheese", "lettuce", "tomatoes", "salsa"],
            "instructions": "1. Cook beef. 2. Warm tortillas. 3. Assemble tacos with toppings.",
            "prep_time": "30 minutes",
            "difficulty": "Medium"
        }
    ]

# Save recipes to JSON file
def save_recipes(recipes):
    with open('recipes.json', 'w') as f:
        json.dump(recipes, f, indent=2)

# Search for recipes by ingredients
def search_recipes_by_ingredients(search_ingredients, recipes, match_all=False):
    if not search_ingredients:
        return recipes
    
    search_ingredients = [ing.lower().strip() for ing in search_ingredients if ing.strip()]
    results = []
    
    for recipe in recipes:
        recipe_ingredients = [ing.lower() for ing in recipe['ingredients']]
        
        if match_all:
            # Match ALL ingredients (strict)
            if all(any(ing in recipe_ingredient for recipe_ingredient in recipe_ingredients) 
                   for ing in search_ingredients):
                # Calculate match percentage
                match_count = sum(1 for ing in search_ingredients 
                                if any(ing in recipe_ingredient for recipe_ingredient in recipe_ingredients))
                match_percentage = (match_count / len(search_ingredients)) * 100
                results.append((recipe, match_percentage))
        else:
            # Match ANY ingredients (flexible)
            matches = []
            for ing in search_ingredients:
                # Check for exact or partial matches
                matched = False
                for recipe_ing in recipe_ingredients:
                    if ing in recipe_ing or recipe_ing in ing:
                        matches.append(ing)
                        matched = True
                        break
                if matched:
                    continue
            
            if matches:
                match_percentage = (len(matches) / len(search_ingredients)) * 100
                results.append((recipe, match_percentage))
    
    # Sort by match percentage (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Return only the recipes (not the percentages)
    return [recipe for recipe, _ in results]

# Get ingredient suggestions
def get_ingredient_suggestions(query, recipes):
    if not query or len(query) < 2:
        return []
    
    query = query.lower().strip()
    all_ingredients = set()
    for recipe in recipes:
        for ingredient in recipe['ingredients']:
            all_ingredients.add(ingredient.lower())
    
    # Find matches
    matches = []
    for ingredient in all_ingredients:
        if query in ingredient:
            matches.append(ingredient)
        elif ingredient.startswith(query):
            matches.append(ingredient)
    
    # Use difflib for close matches
    close_matches = get_close_matches(query, list(all_ingredients), n=5, cutoff=0.6)
    for match in close_matches:
        if match not in matches:
            matches.append(match)
    
    return sorted(matches)[:10]  # Return top 10 suggestions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        match_all = data.get('match_all', False)
        
        recipes = load_recipes()
        results = search_recipes_by_ingredients(ingredients, recipes, match_all)
        
        return jsonify({
            'success': True,
            'recipes': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('q', '')
    recipes = load_recipes()
    suggestions = get_ingredient_suggestions(query, recipes)
    return jsonify({
        'suggestions': suggestions
    })

@app.route('/recipe/<int:recipe_id>')
def get_recipe(recipe_id):
    recipes = load_recipes()
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)
    if recipe:
        return jsonify({
            'success': True,
            'recipe': recipe
        })
    return jsonify({
        'success': False,
        'error': 'Recipe not found'
    }), 404

if __name__ == '__main__':
    # Load and save default recipes if file doesn't exist
    try:
        with open('recipes.json', 'r') as f:
            pass
    except FileNotFoundError:
        default_recipes = get_default_recipes()
        save_recipes(default_recipes)
    
    app.run(debug=True, port=5000)

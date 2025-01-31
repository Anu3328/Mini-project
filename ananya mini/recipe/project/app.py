import os
from flask import Flask, jsonify, render_template, redirect, url_for, request, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/images'


# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['recipe']
users_collection = db['users']
details_collection = db['details']
recipes_collection = db['recipes']


# Home route (redirects to login)
@app.route('/')
def index():
    return redirect(url_for('login'))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Check if email already exists
        if users_collection.find_one({'email': email}):
            flash('Email already exists')
            return redirect(url_for('register'))

        # Hash the password and save user to MongoDB
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': role
        })
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Fetch user from MongoDB
        user = users_collection.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            # Set session for logged-in user
            session['username'] = user['username']
            session['role'] = user['role']

            # Redirect based on role
            if user['role'] == 'Admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('user'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# Admin interface route
@app.route('/admin')
def admin():
    if 'role' in session and session['role'] == 'Admin':
        return render_template('admin.html')
    return redirect(url_for('login'))

# User interface route
@app.route('/user')
def user():
    if 'role' in session and session['role'] == 'User':
        return render_template('user.html')
    return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))


@app.route('/adminform', methods=['GET', 'POST'])
def adminform():
    if request.method == 'POST':
        name = request.form['name']
        time = request.form['time']
        ingredients = request.form['ingredients'].split(',')
        instructions = request.form['instructions'].split(',')
        
        image = request.files['image']
        image_url = save_image(image)
        
        recipes_collection.insert_one({
            'name': name,
            'total_time': time,
            'ingredients': ingredients,
            'instructions': instructions,
            'image_url': image_url
        })
        return redirect(url_for('adminform'))

    recipes = recipes_collection.find()
    return render_template('adminform.html', recipes=recipes)

@app.route('/edit_recipe/<recipe_id>', methods=['POST'])
def edit_recipe(recipe_id):
    updated_name = request.form['name']
    updated_time = request.form['time']
    updated_ingredients = request.form['ingredients'].split(',')
    updated_instructions = request.form['instructions'].split(',')
    updated_image = request.files.get('image')
    
    image_url = None
    if updated_image:
        image_url = save_image(updated_image)

    recipes_collection.update_one({'_id': ObjectId(recipe_id)}, {
        '$set': {
            'name': updated_name,
            'total_time': updated_time,
            'ingredients': updated_ingredients,
            'instructions': updated_instructions,
            'image_url': image_url if image_url else recipes_collection.find_one({'_id': ObjectId(recipe_id)})['image_url']
        }
    })
    return redirect(url_for('adminform'))
def save_image(image_file):
    filename = secure_filename(image_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(file_path)
    return url_for('static', filename=f'images/{filename}')

@app.route('/delete_recipe/<recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    recipes_collection.delete_one({'_id': ObjectId(recipe_id)})
    return redirect(url_for('adminform'))

@app.route('/userform')
def userform():
    recipes = recipes_collection.find()
    return render_template('userform.html', recipes=recipes)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/about1')
def about1():
    return render_template('about1.html')

# @app.route('/turkey')
# def turkey():
#     return render_template('turkey.html')

# @app.route('/turkey1')
# def turkey1():
#     return render_template('turkey1.html')


# @app.route('/greek')
# def greek():
#     return render_template('greek.html')

# @app.route('/saag')
# def saag():
#     return render_template('saag.html')

# @app.route('/pasta')
# def pasta():
#     return render_template('pasta.html')

# @app.route('/spinach')
# def spinach():
#     return render_template('spinach.html')

# @app.route('/kale')
# def kale():
#     return render_template('kale.html')

# @app.route('/avocado1')
# def avocado():
#     return render_template('avocado.html')

# @app.route('/overnight')
# def overnight():
#     return render_template('overnight.html')

# @app.route('/greek1')
# def greek1():
#     return render_template('greek1.html')

# @app.route('/saag1')
# def saag1():
#     return render_template('saag1.html')

# @app.route('/pasta1')
# def pasta1():
#     return render_template('pasta1.html')

# @app.route('/spinach1')
# def spinach1():
#     return render_template('spinach1.html')

# @app.route('/kale1')
# def kale1():
#     return render_template('kale1.html')

# @app.route('/avocado1')
# def avocado1():
#     return render_template('avocado1.html')

# @app.route('/recipe/<name>')
# def recipe_page(name):
#     # Query the MongoDB collection to find the recipe by name
#     recipe = details_collection.find_one({"name": name})
    
#     # Handle case when recipe is not found
#     if recipe is None:
#         return "Recipe not found", 404
    
#     return render_template('recipe.html', recipe=recipe)


@app.route('/recipe/<name>')
def recipe_page(name):
    # Find the recipe by name (case-insensitive match)
    recipe = details_collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    
    if recipe is None:
        return "Recipe not found", 404
    
    return render_template('recipe.html', recipe=recipe)


@app.route('/recipe1/<name>')
def recipe_page1(name):
    # Find the recipe by name (case-insensitive match)
    rec = details_collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    
    if rec is None:
        return "Recipe not found", 404
    
    return render_template('recipe1.html', recipe=rec)




@app.route('/search_ajax', methods=['GET'])
def search_ajax():
    search_query = request.args.get('query')
    
    if search_query:
        # Perform a case-insensitive regex search on the 'name' field
        recipes = details_collection.find({"name": {"$regex": f"^{search_query}", "$options": "i"}})
        
        # Return a list of recipe names and their respective IDs to the frontend
        recipe_data = [{"name": recipe['name'], "id": str(recipe['_id'])} for recipe in recipes]
        return jsonify(recipe_data)
    
    return jsonify([])  # Return an empty list if no query is provided


if __name__ == '__main__':
    app.run(debug=True)

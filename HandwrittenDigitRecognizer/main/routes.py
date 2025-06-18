from flask import render_template
from . import main

@main.route('/')
def index():
    """
    Render the index (landing) page.
    """
    return render_template('index.html')

@main.route('/home')
def home():
    """
    Render the home page after login.
    """
    return render_template('home.html')
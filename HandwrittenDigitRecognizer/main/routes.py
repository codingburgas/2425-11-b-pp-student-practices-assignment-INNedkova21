from flask import render_template
from . import main

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/home')
def home():
    return render_template('home.html')
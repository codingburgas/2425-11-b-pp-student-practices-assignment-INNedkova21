from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import main


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/home')
def home():
    return render_template('home.html')
from flask import render_template
from . import errors

@errors.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@errors.app_errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
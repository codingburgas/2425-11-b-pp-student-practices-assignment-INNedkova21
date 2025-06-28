from flask import Blueprint

feedback = Blueprint('feedback', __name__, template_folder='templates', static_folder='static', static_url_path='/feedback/static')

from . import routes
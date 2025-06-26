from flask import Blueprint

ai = Blueprint('ai', __name__, template_folder='templates', static_folder='static', static_url_path='/ai/static')

from . import routes
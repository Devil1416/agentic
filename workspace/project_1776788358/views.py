# This is the views file
from app import app
@app.route('/user/<username>')
def show_user(username):
    return 'User %s' % username
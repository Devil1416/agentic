# This is the main application file
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return 'Hello, World!'
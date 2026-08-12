import json


from flask import Flask
from flask import render_template

with open("products.json", "r", encoding="utf-8") as file:
    product_list = json.load(file)
app = Flask(__name__)
@app.route('/')
def hello():
    return render_template('index.html', products=product_list)
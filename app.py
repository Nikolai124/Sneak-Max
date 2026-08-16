import json


from flask import Flask
from flask import render_template


with open("products.json", "r", encoding="utf-8") as file:
    product_list = json.load(file)
with open("quiz.json", "r", encoding="utf-8") as file:
    quiz_list = json.load(file)
app = Flask(__name__)
@app.route('/')
def main():
    return render_template('index.html', products=product_list), render_template('index.html',quiz=quiz_list)
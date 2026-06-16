import os
import requests
import psycopg2

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from psycopg2.extras import RealDictCursor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from twse_ranking import get_twse_ranking
from datetime import datetime


load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

db = SQLAlchemy(app)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/html_tags")
def html_tags():
    return render_template("html_tags.html")


@app.route("/todo")
def todo():
    todos = Todo.query.all()
    return render_template("todo.html", todos=todos)


@app.route("/add", methods=["POST"])
def add_todo():
    content = request.form.get("content")

    if content:
        new_todo = Todo(content=content)
        db.session.add(new_todo)
        db.session.commit()

    return redirect("/todo")


@app.route("/update/<int:id>", methods=["POST"])
def update_todo(id):
    todo = Todo.query.get(id)

    if todo:
        new_content = request.form.get("content")

        if new_content:
            todo.content = new_content
            db.session.commit()

    return redirect("/todo")


@app.route("/news")
def news():
    url = "https://news.ycombinator.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    titles = soup.select(".titleline a")

    news_list = []

    for title in titles:
        news_list.append({
            "title": title.text,
            "url": title["href"]
        })

    return render_template(
        "news.html",
        news_list=news_list
    )


@app.route("/quotes")
def quotes():
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    quote_list = []

    try:
        driver.get("https://quotes.toscrape.com/js/")

        quote_elements = driver.find_elements(
            By.CLASS_NAME,
            "quote"
        )

        for quote in quote_elements:
            text = quote.find_element(
                By.CLASS_NAME,
                "text"
            ).text

            author = quote.find_element(
                By.CLASS_NAME,
                "author"
            ).text

            quote_list.append({
                "text": text,
                "author": author
            })

    finally:
        driver.quit()

    return render_template(
        "quotes.html",
        quote_list=quote_list
    )


@app.route("/stock")
def stock_dashboard():
    return render_template("stock.html")


@app.route("/api/stock/<stock_id>")
def get_stock_data(stock_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT date::text, close_price, ma20, upper_band, lower_band
            FROM stock_analysis
            WHERE stock_id = %s
            ORDER BY date ASC
        """, (stock_id,))

        rows = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": rows
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/twse-ranking")
def twse_ranking():
    ranking_data = get_twse_ranking()

    return render_template(
        "twse_ranking.html",
        ranking_data=ranking_data,
        update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
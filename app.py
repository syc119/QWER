import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

import requests
import pandas as pd
from flask import render_template # 確保有匯入 render_template

load_dotenv()

# 初始化 Flask (確保你原本的 app 定義還在)
# app = Flask(__name__) 

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    # 使用 RealDictCursor，讓 PostgreSQL 撈出來的資料自動變成「字典格式」，方便前端轉成 JSON API
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(
        db.String(200),
        nullable=False
    )

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

    return render_template(
        "todo.html",
        todos=todos
    )

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

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    titles = soup.select(".titleline a")

    result = ""

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

    return result
    

@app.route("/quotes")
def quotes():
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://quotes.toscrape.com/js/")

        quote_elements = driver.find_elements(
            By.CLASS_NAME,
            "quote"
        )

        quote_list = []

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

    # 1. 新增專題圖表網頁的路由
@app.route('/stock')
def stock_dashboard():
    """導向新建立的股市分析儀表板"""
    return render_template('stock.html')

# 2. 新增提供資料的 API 路由
@app.route('/api/stock/<stock_id>')
def get_stock_data(stock_id):
    """資料 API：傳回給前端 Chart.js 畫圖用的 JSON 數據"""
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
        
        return jsonify({"success": True, "data": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 新增這個路由
@app.route('/stock_ranking')
def stock_ranking():
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/BFT41U"
    params = {'response': 'json'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200 and response.json().get('stat') == 'OK':
            data = response.json()
            columns = data.get('fields', [])
            rows = data.get('data', [])
            
            # 將資料打包成字典清單，方便前端 HTML 用迴圈讀取
            stock_list = []
            for row in rows:
                stock_list.append(dict(zip(columns, row)))
                
            # 只取前 20 筆排名，避免網頁太長
            stock_list = stock_list[:20] 
            
            return render_template('stock_ranking.html', stock_list=stock_list, columns=columns)
        else:
            return render_template('stock_ranking.html', error="無法從證交所取得正確資料")
    except Exception as e:
        return render_template('stock_ranking.html', error=f"連線發生錯誤: {str(e)}")
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)
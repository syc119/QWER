from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return """<html>
            <head>
                <title>首頁</title>
            </head>
            <body>
                <h1>歡迎來到我的網站</h1>
                <p>這是用 Flask 直接回傳 HTML</p>

                <a href="/about">前往 About</a>
            </body>
        </html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)
import os
import requests
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# 載入你目錄中的 .env 檔案
load_dotenv()

# 從環境變數讀取資料庫連線網址（Render 的 PostgreSQL 或本地測試網址）
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("錯誤：找不到 DATABASE_URL，請檢查你的 .env 檔案！")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """初始化資料庫：建立用於存放分析資料的資料表"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_analysis (
            id SERIAL PRIMARY KEY,
            stock_id VARCHAR(10) NOT NULL,
            date DATE NOT NULL,
            close_price NUMERIC NOT NULL,
            ma20 NUMERIC,
            upper_band NUMERIC,
            lower_band NUMERIC,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_stock_date UNIQUE (stock_id, date)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("【資料庫】stock_analysis 資料表初始化/確認成功。")

def fetch_and_analyze(stock_id="2330"):
    """爬取動態網頁 API 並進行布林通道（標準差）數學統計分析"""
    print(f"【爬蟲】開始抓取股票代碼 {stock_id} 的動態歷史數據...")
    
    # 攔截自 Yahoo 股市前端非同步載入的歷史 K 線 API (獲取近一個月數據)
    # ======= 請替換這段程式碼 =======
    # 改用更穩定的新版動態 API 網址結構
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_id}.TW?range=1mo&interval=1d"
    
    # 補上更完整的瀏覽器偽裝標頭，防止被 Yahoo 的 CDN 阻擋
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://tw.stock.yahoo.com",
        "Referer": "https://tw.stock.yahoo.com/"
    }
    # ===============================
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ 錯誤：無法取得 API 資料 (HTTP {response.status_code})")
            return
            
        json_data = response.json()
        
        # --- 新版 JSON 結構動態解析 ---
        result = json_data.get("chart", {}).get("result", [])
        if not result:
            print("❌ 錯誤：動態 API 回傳的 K 線資料為空。")
            return
            
        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
        close_prices = indicators.get("close", [])
        
        # 轉換為 Pandas DataFrame 
        df = pd.DataFrame({
            "date": pd.to_datetime(timestamps, unit="s").date,  # 時間戳轉日期
            "close": close_prices
        })
        
        # 剔除空值並排序
        df = df.dropna().sort_values('date').reset_index(drop=True)
        df['close'] = df['close'].astype(float)
        
        # === 數學與資料分析核心 (統計學標準差應用) ===
        # 1. 計算 20 日移動平均線 (MA)
        df['MA20'] = df['close'].rolling(window=20).mean()
        # 2. 計算 20 日收盤價的「標準差 (Standard Deviation)」
        df['STD20'] = df['close'].rolling(window=20).std()
        
        # 3. 布林通道公式：均線 +/- (2 * 標準差)
        df['Upper_Band'] = df['MA20'] + (2 * df['STD20'])
        df['Lower_Band'] = df['MA20'] - (2 * df['STD20'])
        
        # 去除前 19 天因資料不足無法計算出 MA 與標準差的 NaN 空值
        df = df.dropna().reset_index(drop=True)
        
        # === 將資料大量存入 PostgreSQL ===
        conn = get_db_connection()
        cur = conn.cursor()
        
        insert_data = [
            (stock_id, row['date'], row['close'], row['MA20'], row['Upper_Band'], row['Lower_Band'])
            for _, row in df.iterrows()
        ]
        
        upsert_query = """
            INSERT INTO stock_analysis (stock_id, date, close_price, ma20, upper_band, lower_band)
            VALUES %s
            ON CONFLICT (stock_id, date) 
            DO UPDATE SET 
                close_price = EXCLUDED.close_price,
                ma20 = EXCLUDED.ma20,
                upper_band = EXCLUDED.upper_band,
                lower_band = EXCLUDED.lower_band;
        """
        
        execute_values(cur, upsert_query, insert_data)
        conn.commit()
        cur.close()
        conn.close()
        print(f"✨ 股票 {stock_id} 統計資料已成功存入 PostgreSQL 數據庫！")
        
    except Exception as e:
        print(f"❌ 執行爬蟲或分析時發生異常: {str(e)}")

if __name__ == "__main__":
    init_db()
    # 預設幫你跑「台積電 2330」與「鴻海 2317」當作初始測試資料
    fetch_and_analyze("2330")
    fetch_and_analyze("2317")
from datetime import datetime, timedelta
import pandas as pd
import requests


def get_latest_workday():
    """自動計算最接近的可能交易日（考慮到今天還沒收盤或週末）"""
    now = datetime.now()

    # 如果是今天下午 15:30 之前，先退回昨天（因為今天的盤後資料還沒出來）
    if now.hour < 15 or (now.hour == 15 and now.minute < 30):
        now -= timedelta(days=1)

    # 如果退回後是禮拜日(6)，再退 2 天到禮拜五
    if now.weekday() == 6:
        now -= timedelta(days=2)
    # 如果退回後是禮拜六(5)，再退 1 天到禮拜五
    elif now.weekday() == 5:
        now -= timedelta(days=1)

    return now.strftime("%Y%m%d")


def get_twse_ranking():
    """爬取證交所發行量加權股價指數成分股當日成交量值最高前二十名排行 (BFT41U)"""
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/BFT41U"

    # 自動取得正確的查詢日期（格式：YYYYMMDD）
    target_date = get_latest_workday()
    print(f"🔄 正在嘗試爬取證交所日期：{target_date} 的排行資料...")

    # 設定請求參數
    params = {
        "response": "json",
        "date": target_date,  # 帶入動態日期，避免盤中或假日抓不到資料
    }

    # 模擬瀏覽器標頭，避免被證交所阻擋
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.twse.com.tw/zh/",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # 檢查證交所回傳狀態是否為 OK
            if data.get("stat") == "OK":
                columns = data.get("fields", [])
                rows = data.get("data", [])

                # 轉換為 Pandas DataFrame
                df = pd.DataFrame(rows, columns=columns)

                # 💡 核心優化：清理欄位名稱中的 <br> 標籤（例如 "證券<br>代號" -> "證券代號"）
                df.columns = [col.replace("<br>", "") for col in df.columns]

                print(f"✅ 成功抓取到 {target_date} 的資料！共 {len(df)} 筆。")
                print(df.head(5))  # 在終端機先印出前五筆檢查

                # 將 DataFrame 轉換為 List of Dicts，方便 Flask 前端使用
                return df.to_dict(orient="records")

            else:
                print(f"⚠️ 證交所回傳訊息: {data.get('stat')}")
                # 如果當天剛好是補班日或特殊沒開盤日，嘗試改抓「不帶日期」的預設最新資料
                return get_twse_ranking_fallback(headers)
        else:
            print(f"❌ 網路請求失敗，狀態碼: {response.status_code}")
            return None

    except Exception as e:
        print(f"💥 發生非預期錯誤: {e}")
        return None


def get_twse_ranking_fallback(headers):
    """備用方案：如果指定日期失敗，改抓證交所預設最新一筆資料"""
    url
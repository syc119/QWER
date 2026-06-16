import requests
import pandas as pd

def get_twse_ranking():
    # 這是證交所首頁常用來獲取「成交量/成交值/漲跌幅」排行資料的盤後 API 網址
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/BFT41U"
    
    # 設定請求參數 (預設抓最新資料，也可以指定 date=20260616)
    params = {
        'response': 'json',
    }
    
    # 模擬瀏覽器標頭，避免被證交所阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("正在從證交所抓取最新排行資料...")
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('stat') == 'OK':
            columns = data.get('fields', [])
            rows = data.get('data', [])
            
            # 轉換為 Pandas DataFrame 表格
            df = pd.DataFrame(rows, columns=columns)
            
            print("\n 成功取得排行資料！前 10 筆顯示：")
            print(df.head(10).to_string()) # to_string() 可以讓終端機排版更整齊
            
            # 自動儲存成 CSV
            df.to_csv("twse_ranking_result.csv", index=False, encoding="utf-8-sig")
            print("\n 資料已儲存至：twse_ranking_result.csv")
        else:
            print(f"證交所回傳錯誤: {data.get('stat')}")
    else:
        print(f"無法連線到證交所，錯誤代碼: {response.status_code}")

if __name__ == "__main__":
    get_twse_ranking()
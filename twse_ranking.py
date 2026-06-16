from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime


def get_twse_ranking():
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.twse.com.tw/zh/#ranking")

        wait = WebDriverWait(driver, 20)

        wait.until(
            EC.presence_of_element_located(
                (By.TAG_NAME, "table")
            )
        )

        rows = driver.find_elements(
            By.CSS_SELECTOR,
            "table tbody tr"
        )

        data = []

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")

            if len(cols) >= 4:
                code = cols[0].text.strip()
                name = cols[1].text.strip()
                value = cols[2].text.strip()

                if code.isdigit() and name and value:
                    data.append({
                        "rank": len(data) + 1,
                        "code": code,
                        "name": name,
                        "value": value
                    })

            if len(data) == 10:
                break

        return data

    except Exception as e:
        print("TWSE 爬蟲錯誤:", e)
        return []

    finally:
        driver.quit()
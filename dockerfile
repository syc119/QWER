# 以 Python 3.11 的輕量版映像檔作為基底
FROM python:3.11-slim

# 把容器內的工作目錄設成 /app
# 後面的操作都會在這個資料夾進行
WORKDIR /app

# 把本機的 requirements.txt 複製到容器裡
COPY requirements.txt .

# 在容器中安裝 Flask
RUN pip install --no-cache-dir -r requirements.txt

# 把目前專案資料夾裡的內容全部複製進容器
COPY . .

# 容器啟動後，自動執行 python app.py
CMD ["python", "app.py"]
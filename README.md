# 台灣健保藥品給付規定查詢系統 (Taiwan NHI Drug Regulations Query Engine)

本系統為專為台灣健保藥品給付規定設計之 **Google OKF 相容知識庫查詢與雙語 ATC / 疾病跨搜尋引擎**。包含雙平台 Web 應用程式：
1. **桌面版大螢幕網頁 (Desktop Web App)**: `http://localhost:5001/`
2. **智慧型手機行動版 App (Mobile Smartphone Web App)**: `http://localhost:5001/mobile`

---

## 🚀 部署與託管方式 (Deployment & Hosting Options)

本專案已封裝完畢，支援多種正式生產環境（Production）部署與託管方式：

### 方式 1: 使用 Docker Compose (一鍵部署，推薦)
適合具備 Docker 環境之 Linux / macOS / Windows 伺服器：
```bash
# 啟動服務 (背景執行)
docker-compose up -d --build

# 查看執行狀態
docker-compose ps

# 停止服務
docker-compose down
```

---

### 方式 2: 使用原生 Docker 容器部署
```bash
# 建立 Docker 鏡像
docker build -t nhi-regulations-app .

# 運行容器
docker run -d -p 5001:5001 --name nhi_app nhi-regulations-app
```

---

### 方式 3: Shell 一鍵腳本部署 (Linux VPS / macOS)
```bash
# 賦予執行權限並執行
chmod +x deploy.sh
./deploy.sh
```

---

### 方式 4: 傳統 Python + Gunicorn 手動部署
```bash
# 1. 安裝套件
pip install -r requirements.txt

# 2. 解析最新給付規定文件建置 OKF 知識庫
python3 -m backend.parser

# 3. 啟動生產級 Gunicorn WSGI 伺服器
gunicorn --bind 0.0.0.0:5001 --workers 4 --threads 2 wsgi:app
```

---

## 雲端託管平台 (Cloud Hosting Providers)

- **Google Cloud Run / AWS App Runner / GCP App Engine**:
  直接連接本專案 GitHub 儲存庫，平台將自動讀取 `Dockerfile` 完成自動建置與無伺服器（Serverless）部署。
- **Heroku / DigitalOcean App Platform / Render**:
  選擇 `Python` 環境，啟動指令設定為 `gunicorn --bind 0.0.0.0:$PORT wsgi:app` 即可。

---

## 📁 專案架構說明 (Project Structure)

```
NHI_Drug_Regulations/
├── backend/                # 後端核心引擎 (Flask, Parser, Indexer, ATC, Disease Engine)
├── okf_data/               # Google OKF 相容 YAML 知識庫資料集
├── public/                 # 前端靜態資源 (HTML, CSS, JS 包含桌面與手機行動版)
├── uploads/                # 使用者上傳給付規定 Word/PDF 暫存目錄
├── Dockerfile              # Docker 容器構建檔
├── docker-compose.yml      # Docker Compose 容器編排檔
├── requirements.txt        # Python 生產環境依賴清單
├── wsgi.py                 # WSGI 生產伺服器進入點
├── deploy.sh               # 一鍵部署 Shell 腳本
└── README.md               # 部署說明文件
```

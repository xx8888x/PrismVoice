# 稜鏡 Prism

Vue 3 + Laravel 12 + Python + MariaDB 的本機新聞觀點工作台。專案位置：D:\稜鏡媒體網站\Site。

## 架構說明 (雙軌架構)

- **前端 (Vue 3)**: 提供「Don't make me think」極簡風格的觀點比對介面與時間軸趨勢。
- **後端 API (Laravel 12 / PHP)**: 負責快速響應前端請求並從資料庫讀取整理好的事件資料。
- **爬蟲與 AI 處理 (Python)**: 在背景執行，負責自動抓取多方新聞 (UDN, Yahoo, PTS) 全文，進行動態事件分群 (Event Clustering)，並透過 Mock AI 進行立場評估與極端偏誤警報 (Webhook)。
- **資料庫 (MariaDB)**: 作為 PHP 與 Python 之間解耦的共用核心。

## 開啟

PowerShell 執行：

`powershell
cd D:\稜鏡媒體網站\Site
.\start.ps1
`

這會一鍵在背景自動啟動 **MariaDB**、**PHP 伺服器** 以及 **Python 爬蟲服務**。
瀏覽 http://127.0.0.1:8088。關閉服務用 .\stop.ps1。

## 功能亮點

- **多方媒體聚合**：自動從多個 RSS 來源獲取新聞（聯合、Yahoo、公視），實現真正的跨媒體比對。
- **自動事件分群 (Clustering)**：Python 會比對新聞標題相似度，將同一個社會事件自動歸類。
- **Mock AI 立場評估**：自動對新聞內文與標題進行立場評估（支援、中立、反對）。未來可輕易替換為真實 LLM API (如 Gemini / OpenAI)。
- **時間軸趨勢與極端警報**：時間軸直觀顯示新聞偏向的轉變軌跡；當 AI 偵測到極端立場文章時，支援透過 Webhook 發送警告。

## 舊版手動匯入已棄用

舊版的 import-news.ps1 已經移除。系統現在完全依賴 Python 服務的即時爬取與智慧分群功能。

## 開發

`powershell
cd D:\稜鏡媒體網站\Site\backend
npm install
npm run build
`

Vue 原始碼在 ackend/resources/js/App.vue。
Python 服務位於 python_service/main.py，會自動讀取 ackend/.env 中的資料庫帳密。

# 稜鏡 Prism

Vue 3 + Laravel 12 + Python + MariaDB 的本機新聞觀點工作台。專案位置：D:\稜鏡媒體網站\Site。

## 架構說明

- **前端 (Vue 3)**: 提供「Don't make me think」極簡風格的觀點比對介面與時間軸趨勢。
- **後端 API (Laravel 12 / PHP)**: 擁有資料表結構（migrations），負責 API、人工標註與比較判定。不再自己抓 RSS。
- **擷取管線 (Python, `python_service/`)**: **唯一**的新聞擷取路徑。依 `sources` 資料表抓 RSS → 抓全文 → 依網址去重 → 轉載偵測 → 事件分群 → 標題規則初評，全部標為 `unreviewed`。
- **共用定義 (`shared/`)**: `perspective.json` 是觀點維度與標題規則的唯一定義，PHP 與 Python 都讀它；`perspective_cases.json` 由兩邊的測試共同驗證，確保判定一致。
- **資料庫 (MariaDB)**: 作為 PHP 與 Python 之間解耦的共用核心。

### 資料表

| 表 | 用途 |
|---|---|
| `sources` | 每個 RSS 來源一列：網址、媒體類型、`link_pattern`（文章網址白名單與版面篩選）、全文選擇器、`pubdate_offset_minutes`（校正時區標錯的 feed，目前只有 Yahoo = 480）、抓取頻率與健康狀態（連續失敗會指數退避）。刻意不存政治光譜標籤，光譜要從文章資料量測。 |
| `news_events` / `articles` | 事件與報導；`articles.source_id` 指向 `sources`，`source` 欄位保留顯示名稱。`articles.duplicate_of_article_id` 有值代表轉載稿，指向同組最早的原稿（一律直接指向原稿，不會串成鏈）。 |
| `article_contents` | 全文（僅供內部分析，API 不輸出）、字數、雜湊、`simhash`（轉載比對用的指紋；NULL 代表還沒比對或內文太短）、擷取方式與狀態（`ok` / `empty` / `failed`）。 |

目前啟用 11 個來源：聯合新聞網、中央社、自由時報、公視、ETtoday、新頭殼、風傳媒、報導者、Yahoo（政治版，多為轉載）、BBC中文、德國之聲中文。台灣事實查核中心已建檔但停用，等主張比對功能完成後再開。新增來源直接在 `sources` 表加一列即可。

## 開啟

PowerShell 執行：

```powershell
cd D:\稜鏡媒體網站\Site
.\start.ps1
```

這會一鍵在背景自動啟動 **MariaDB**、**PHP 伺服器** 以及 **Python 擷取服務**。
瀏覽 http://127.0.0.1:8088。關閉服務用 .\stop.ps1。

第一次更新到這個版本，先跑資料表遷移，再幫舊文章補做轉載比對：

```powershell
cd D:\稜鏡媒體網站\Site\backend
..\.runtime\php\php.exe artisan migrate
cd ..\python_service
pip install -r requirements.txt
python main.py --backfill-content
```

## 功能亮點

- **多方媒體聚合**：11 個 RSS 來源，含全文擷取（各站優先用 `content_selector`，否則用段落密度判斷內文）。選擇器可以選容器或直接選段落，所有符合的元素都會收進來；目前聯合新聞網、BBC 中文、Yahoo 有設定，Yahoo 用 `:not(.read-more-vendor)` 排除文末「更多…報導」連結，否則轉載會漏判。
- **自動事件分群**：以標題字元雙字組（IDF 加權）比對 ±3 天內的報導；寧可少併、不可錯併。比對前先把標題轉成台灣繁體（OpenCC `s2tw`，「臺」統一成「台」），德國之聲的簡體標題才對得上。示範事件不參與分群。
- **轉載偵測**：聯合新聞網、Yahoo 常一字不改轉載中央社、自由時報的稿件。匯入時先用內文 SimHash 粗篩（漢明距離 ≤ 20），再用 4 字元片段精確確認（Jaccard ≥ 0.5，且較短那篇 ≥ 80% 出現在另一篇），而且兩篇標題至少要有 3 個相同的雙字組（避免全文擷取抓錯區塊時，把兩篇不相干的報導當成轉載）。各家一字不改貼同一份政院新聞稿，也會被標成同一組，原稿就是最早貼出的那篇。確認是轉載，就把 `duplicate_of_article_id` 指向最早的原稿，並放進原稿所在的事件。如果原稿比較晚才抓到（例如中央社排在聯合新聞網之後才抓），會改由它當原稿；發布時間相同時，先抓到的那篇當原稿。內文少於 200 字不比對。`/api/events/{id}` 的每篇文章都帶這個欄位，前端可以把轉載稿收合。事件清單的 `articles_count` 目前仍把轉載稿算進去。
- **初步評估**：只用標題規則判「討論焦點」與「表達方式」，「主張方向」一律留給人工；自動結果一律標為 `unreviewed`。未來接 LLM 時只需替換 Python 端的評估函式。
- **時間軸趨勢與警報**：時間軸直觀顯示新聞偏向的轉變軌跡；設定 `PRISM_ALERT_WEBHOOK_URL`（環境變數或 `backend/.env`）後，強烈判定（±2、信心 ≥ 0.6）會推播。未設定時不送出任何資料。

## 介面說明（Don't Make Me Think）

- **結論先行**：比較頁最上方一句話告訴你「辨識到相反主張／觀點不同，但未達對立／尚無法判定」。
- **A 永遠藍、B 永遠橘**：卡片、地圖標記、時間軸標籤一致；用「換一篇…」更換、⇄ 交換。
- **觀點地圖**：三個維度，軸兩端是白話方向，下方直接寫出「明確支持／肯定・信心 100%」這類可讀判定；「判定依據」展開看主張者、引文、理由。
- **報導時間軸**：每篇都有「設為 A」「設為 B」「覆核標註」。
- **覆核標註**：對話框用 −2…+2 五格打分；選「待判定」就不必填其他欄位。儲存走 `PATCH /api/articles/{id}`，版本衝突（409）會提示重新載入。
- 手機版：左上角選單開啟事件清單。

## 擷取服務指令

```powershell
cd D:\稜鏡媒體網站\Site\python_service
python main.py                     # 常駐（start.ps1 會啟動）：每分鐘檢查哪些來源到期
python main.py --once              # 只跑一輪到期的來源
python main.py --source cna        # 立即抓取指定來源
python main.py --backfill-content  # 補抓還沒有全文的舊文章，再幫還沒比對過的內文補做轉載比對（不會移動事件）
```

舊版的 `import-news.ps1` 與 Laravel 的 `news:import` 指令都已移除。

## 開發與測試

```powershell
cd D:\稜鏡媒體網站\Site\backend
npm install
npm run build
```

- Vue 原始碼在 `backend/resources/js/App.vue`。
- Python 服務位於 `python_service/`，會自動讀取 `backend/.env` 中的資料庫帳密。
- Python 測試：在 `python_service` 執行 `python -m unittest discover -s tests -t .`
- Laravel 測試：`php artisan test`。PHPUnit 無法讀取含中文的路徑，請從英文路徑的 junction 執行（例如 `New-Item -ItemType Junction -Path C:\prism -Target D:\稜鏡媒體網站\Site`，再到 `C:\prism\backend` 執行）。

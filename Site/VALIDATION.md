# 驗證紀錄

- Vue / Vite production build 成功。
- 使用專用 `mediaweb_test` MariaDB 資料庫執行 PHPUnit：10 個測試通過，28 個斷言。
- 測試範圍：對立判定閾值、資料不足保留未知、語氣差異不冒充立場對立、RSS 去重保留人工標註、時間軸排序、同事件限制、標註必填依據、revision 衝突防護、示範資料隔離、移動重設標註、無效來源與日期拒絕。
- 本機首頁與 `/api/events` HTTP 200，真實樣本 24 篇、14 個事件。
- 未執行瀏覽器視覺／點擊自動化測試。
- WebMCP 採 feature detection，提供事件讀取與切換比較工具；本環境未提供可驗證的 WebMCP registry，因此未宣稱完成 WebMCP 瀏覽器整合驗證。不支援 WebMCP 的瀏覽器仍可正常操作。
- 樣本僅 RSS 標題與中繼資料，沒有全文語意模型或已校準的概率；真實主張需人工判定。

- 最終實際 HTTP 驗證：首頁 200；示範文章比較回傳 opposed / 主張方向；缺少 CSRF 回傳 419；合法 CSRF 搭配舊 revision 回傳 409，未修改標註。

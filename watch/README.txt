每日另存網頁操作說明 (Daily snapshot instructions)
====================================================

目的
----
Claude 每天會比對這個資料夾裡的網頁存檔, 跟 Excel 表格裡記錄的版本做比對。
如果官網版本有變, Claude 會自動更新 Taichi_Driver_Utility_BIOS_Versions.xlsx
並通知您; 如果您今天忘記存檔, Claude 會提醒您。

每天要做的事
------------
用瀏覽器(Chrome 或 Edge)打開以下兩個網址, 每個頁面都要做一次「另存新檔」:

1. X870E Taichi
   網址: https://www.asrock.com/mb/AMD/X870E%20Taichi/index.tw.asp
   存檔方式: Ctrl+S, 存檔類型選「網頁, 完整」(Webpage, Complete)
   檔名務必打成: X870E Taichi
   存檔位置: watch\X870E Taichi\ (也就是這個 README 所在資料夾下的 "X870E Taichi" 子資料夾)
   存檔後應該會產生:
     watch\X870E Taichi\X870E Taichi.html
     watch\X870E Taichi\X870E Taichi_files\ (附屬資源, 可忽略不用管)

2. Z890 Taichi
   網址: https://www.asrock.com/mb/Intel/Z890%20Taichi/index.tw.asp
   存檔方式: Ctrl+S, 存檔類型選「網頁, 完整」(Webpage, Complete)
   檔名務必打成: Z890 Taichi
   存檔位置: watch\Z890 Taichi\
   存檔後應該會產生:
     watch\Z890 Taichi\Z890 Taichi.html
     watch\Z890 Taichi\Z890 Taichi_files\

注意事項
--------
1. 檔名跟資料夾位置一定要固定, 程式是用固定路徑去讀檔, 檔名打錯或存錯資料夾, Claude 會偵測不到新檔案。
2. 如果瀏覽器問「要取代現有檔案嗎」, 選是, 直接覆蓋掉昨天的存檔即可。
3. 只存主頁面就好, 不需要特別點到下載分頁, 頁面本身已經包含 BIOS / Utility / Driver 完整資料。
4. 存檔時間不拘, 但建議在 Claude 排程提醒的時間點附近操作, 比對才會即時。

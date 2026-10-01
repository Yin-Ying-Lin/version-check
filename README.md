# ASRock 主機板版本追蹤(X870E Taichi / Z890 Taichi)

## 目的

自動追蹤 ASRock 官網上 X870E Taichi 與 Z890 Taichi 兩款主機板的 Utility、Driver、BIOS 版本資訊, 有更新時更新 Excel 表格並通知使用者。

## 資料夾結構

```
Driver Version Update\
  README.md                                   本說明文件
  Taichi_Driver_Utility_BIOS_Versions.xlsx     版本總表, 分頁為 X870E Taichi 與 Z890 Taichi
  scripts\
    parse_page.py        解析另存網頁, 取出 Utility / Driver / BIOS 版本資料
    diff_and_update.py   比對新舊版本, 有變動時更新 Excel 並回報結果
    daily_check.py        每日排程實際呼叫的進入點, 純 Python, 不經過 Claude
    notify_toast.ps1      顯示 Windows 原生通知(toast), 不經過 Claude
    state.json             記錄目前已知的版本基準, 由程式自動維護, 不需手動編輯
  watch\
    README.txt             每日存檔操作說明(網址、檔名、存放位置)
    X870E Taichi\X870E Taichi.html
    Z890 Taichi\Z890 Taichi.html
```

## Excel 表格說明

每個分頁(X870E Taichi、Z890 Taichi)內含三個表格區塊, Utility、Driver、BIOS, 欄位為軟體名稱、版本、日期、備註。另有一欄 MatchKey, 預設隱藏, 是程式自動比對用的識別鍵, 格式為「名稱 作業系統 Beta狀態」, 請勿手動修改, 否則自動更新會對不到該列而失敗。

第一個分頁 meta 記錄資料擷取日期與來源說明。

## 每日操作流程(使用者端)

官網有防爬蟲機制(Incapsula), 無法由程式自動背景連線取得資料, 所以需要使用者每天手動操作一次:

1. 用瀏覽器開啟 watch\README.txt 內列出的兩個網址
2. 用 Ctrl+S 另存新檔, 存檔類型選「網頁, 完整」
3. 檔名與存放資料夾務必固定(見 watch\README.txt), 直接覆蓋昨天的檔案

## 自動比對與更新

執行方式:

```
cd scripts
python diff_and_update.py --all
```

行為:

1. 解析今天存的網頁, 跟 state.json 裡記錄的上一次版本做比對
2. Utility / Driver 若版本不同, 直接更新 Excel 對應儲存格
3. BIOS 若有新版本, 自動在表格最上方插入新的一列, 並把「最新版」標記移過去
4. 若當天檔案不是今天存的(忘記存檔), 回報 STALE, 提醒使用者
5. 若找不到存檔, 回報 NO_SOURCE

## 排程

原本用 Claude Code 的 CronCreate 工具排程, 但每次觸發都是在這個對話 session 裡重新執行一次, 會持續耗費 token, 且最長七天就會失效。已改成用 Windows 工作排程器(Task Scheduler)直接執行, 完全不經過 Claude, 不耗 token, 也沒有七天的限制。

設定內容:

1. 工作名稱: ASRock Driver Version Check
2. 觸發時間: 每天 11:00
3. 執行內容: `python.exe scripts\daily_check.py`

daily_check.py 會依序呼叫 diff_and_update.py 比對兩個產品, 有變動或今天忘記存檔時, 用 notify_toast.ps1 跳出 Windows 原生通知, 整個過程不需要 Claude 參與。

如果要修改排程時間或內容, 用 PowerShell 執行:

```
Get-ScheduledTask -TaskName "ASRock Driver Version Check"
Set-ScheduledTask / Unregister-ScheduledTask 視需求調整
```

## 通知方式現況

目前使用 Windows 原生 toast 通知(notify_toast.ps1), 不需要任何 Claude connector 或連線, 純本機彈出視窗提醒。

曾評估過的其他方式, 皆因組織層級限制或隱私疑慮而擱置, 記錄如下供之後參考:

1. Outlook(Microsoft 365 connector): 需要公司 Microsoft 365 租戶管理員核准(Entra ID admin consent), 已請 IT 協助, 尚未核准完成, 之後若核准, 可以直接改用 Python 的 smtplib 搭配應用程式密碼或 Microsoft Graph API 寄信, 不需要再依賴 Claude 的 connector 機制
2. 個人 Gmail: 考慮過當替代方案, 但授權範圍是整個信箱(讀寫皆可), 使用者評估隱私風險不可接受, 已排除
3. Claude Remote Control(手機推播): 組織管理員已開啟此功能, 曾短暫連接測試, 但使用者後續決定取消連接(不確定連到哪支裝置、且跟每日提醒無直接關係, 每日提醒已改用 Windows 原生通知, 不需要 Remote Control), 已停用

## 已知限制

1. 新增 / 移除的 Utility、Driver 項目不會自動增減 Excel 列數, 僅於通知中提示, 需使用者手動處理
2. 官網頁面本身若改版(表格結構變動), parse_page.py 的解析邏輯可能需要相應調整
3. MatchKey 欄位的名稱比對是以官網原始文字為準, 若官網文字本身變動(非版本變動, 而是名稱措辭調整), 可能被誤判為新增項目

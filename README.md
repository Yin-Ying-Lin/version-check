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
    state.json            記錄目前已知的版本基準, 由程式自動維護, 不需手動編輯
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

使用 Claude Code 的 CronCreate 工具, 設定每天本機時間 9:05 自動執行上述比對, 並透過通知告知使用者結果。

注意事項:

1. 排程綁定在建立當下的 session, 最長七天後自動失效, 到期需要重新建立
2. 排程只有在 session 閒置時才會觸發, 需要讓該 session 保持存在

## 通知方式現況

目前使用 PushNotification(終端機 / 手機推播), 原因如下:

1. Email 通知原本規劃用公司 Outlook(Microsoft 365 connector), 但該 connector 需要公司 Microsoft 365 租戶管理員另外核准(Entra ID admin consent), 已請 IT 協助處理, 尚未核准完成
2. 曾考慮改用個人 Gmail 作為替代方案, 但使用者評估後認為隱私風險(授權範圍為整個信箱, 非僅限寄信)不可接受, 已排除此方案

待 Outlook connector 核准完成後, 需開新 session 確認工具可用, 再將排程的通知方式由 PushNotification 切換為 Outlook 寄信。

## 已知限制

1. 新增 / 移除的 Utility、Driver 項目不會自動增減 Excel 列數, 僅於通知中提示, 需使用者手動處理
2. 官網頁面本身若改版(表格結構變動), parse_page.py 的解析邏輯可能需要相應調整
3. MatchKey 欄位的名稱比對是以官網原始文字為準, 若官網文字本身變動(非版本變動, 而是名稱措辭調整), 可能被誤判為新增項目

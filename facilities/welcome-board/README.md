# 校門迎賓看板

使用者確認 S17 外側有長條看板。位置、尺寸、支架與配色為近似；顯示面朝南、面向校門入校方向。S17 無人行道，花圃緣石仍保留。

`board.json` 為獨立設定，無須改道路或建築程式：

- `defaultContent`：平時 Welcome、學校全名、校徽與副標。
- `activeCampaign`：填入 `campaigns` 的活動代號；設 `null` 恢復預設。
- 每個活動可設定 `startsAt`、`endsAt`（含時區 ISO 時間，結束時間不含）及 `content`。未到期或已結束會顯示預設；時間於載入時判斷。
- `content` 可覆寫 welcome/title/subtitle/background/foreground/accent/artwork；未填欄位沿用預設。`artwork` 是此資料夾內的圖片相對路徑，`null` 為純色背景。活動圖置中裁切滿版，覆深色遮罩保留文字可讀性。
- 校徽保持獨立；圖片失敗時保留文字。所有圖片應放在網站內，避免依賴外站。

例如新增活動（以下為設定示例，未啟用）：

```json
"activeCampaign": "anniversary",
"campaigns": {
  "anniversary": {
    "startsAt": "2026-11-01T00:00:00+08:00",
    "endsAt": "2026-12-01T00:00:00+08:00",
    "content": {
      "welcome": "歡迎返校",
      "title": "國立高雄師範大學校慶",
      "subtitle": "燕巢校區 · 歡迎師生與校友",
      "background": "#573048",
      "artwork": "./anniversary.jpg"
    }
  }
}
```

修改後隨專案發布才會讓所有人看到。`setContent` 可在開發預覽時重繪同一張材質，不會增加每幀繪製成本；沒有瀏覽器直接改寫遠端檔案的權限。

校徽與校名組合原圖：[校方頁首圖檔](https://w3.nknu.edu.tw/img/nknu-logo-nbg.png)，由 [校方共用元件](https://w3.nknu.edu.tw/js/components.js) 引用。以原圖的校徽範圍作顯示裁切，未自行仿畫校徽。圖像權利屬原權利人，不隨專案程式授權重新授權。

2026-11-11 補充：`placement: "entrance-road-edge"` 會依入口鋪面北側外邊界計算看板前緣，以圓弧貼齊道路，無須另填離路距離。`position[0]` 控制橫向中心；此模式的縱向位置與朝向由道路決定。支架與底座採實例合批，保持少量繪製呼叫。

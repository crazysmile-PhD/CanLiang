# Reply: BetterGI 1.05 Preview Strategy Follow-up

**To:** Thomas Tseng  
**Subject:** Re: [BetterGI] 關於 1.05 版後自動啟動瀏覽器與 Sunshine 支援計畫的回覆

Thomas 您好，

感謝整理建議。以下是我們的行動規劃，將在下一個迭代逐步落實：

## 1. 自動啟動瀏覽器策略
- 延續 1.05 版起的預設：啟動時不自動開啟瀏覽器，避免與 `yuanshen.exe` / `bettergi.exe` 競奪記憶體。  
- `--open-browser` 參數與設定檔選項保留，改為 **opt-in**，必要時可手動啟用。  
- 文件會補充提醒：在預覽模式為 `none` 時啟用該參數，頁面會顯示占位提示而非串流畫面。

## 2. Sunshine 串流定位
- `--preview-mode` 新增下列選項並沿用預設 `none`：`sunshine`、`web-rtc`、`ll-hls`。  
- Sunshine 模式定位為「本機/同網段低延遲監看」，主流程維持 NVENC/HEVC。  
- 若需瀏覽器即時預覽，將評估 WebRTC (H.264/VP9) 與 LL-HLS (MSE) 原型，並於驗證後決定是否納入正式版本。

## 3. 記憶體測試與保護
- 建立 20 分鐘 soak test：監控 Private Bytes、Working Set、Handle 數與 frame latency。  
- Sunshine 若發現記憶體成長，導入緩衝池與「僅解析度變更時重建資源」策略。  
- 各模式補強極端情境測試（串流中斷、重連、解析度切換）。

## 4. 後續交付
- 近期會提交小型 PR：包含 `--preview-mode` 參數、記憶體防護閾值與相對應測試。  
- WebRTC / LL-HLS 原型與 soak test 腳本將分開提供，以利後續討論與整合。  
- 若有額外的串流內存追蹤數據，也請協助分享，我們將納入分析。

感謝協助，若有進一步的需求或觀察，歡迎隨時告知。

敬祝順心，

BetterGI 團隊

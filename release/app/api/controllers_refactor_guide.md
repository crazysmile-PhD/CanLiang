# `release/app/api/controllers.py` 重構指導文件

本文件紀錄了當前最複雜模組的觀察結果，並概述如何拆分職責、提高可測試性、以及隔離副作用的計畫。

## 目前痛點

### 多個職責混雜在同一檔案中
- `LogController`、`WebhookController`、`StreamController`、`SystemInfoController` 都放在同一模組中，雖然它們分別涉及資料庫持久化、作業系統層級的螢幕擷取、以及系統資源監控等完全不同的領域。【F:release/app/api/controllers.py†L27-L782】

### `StreamController` 同時處理視窗搜尋、畫面擷取與串流邏輯
- 該類別超過 500 行，混雜了列舉視窗、應用遊戲遮罩、擷取畫面、以及串流狀態轉換等功能。【F:release/app/api/controllers.py†L190-L570】

### 直接依賴全域模組與函數
- 例如對 Win32 API、OpenCV、psutil 的直接呼叫，使得單元測試難以替換或模擬這些依賴。【F:release/app/api/controllers.py†L190-L711】

### 視窗列舉邏輯重複
- `find_window_by_process_name` 與 `get_available_programs` 幾乎重複實作了列舉可見視窗的流程與錯誤處理。【F:release/app/api/controllers.py†L200-L265】【F:release/app/api/controllers.py†L604-L707】

## 模組拆分建議

### `app/controllers/logs.py`
- 保留 `LogController`，專注於協調 `LogDataManager` 並回傳 DTO。
- 將 DTO 格式化的輔助函式（如 `reverse()`）搬入此模組以維持內聚。【F:release/app/api/controllers.py†L27-L86】

### `app/controllers/webhooks.py`
- 放置 `WebhookController`，將資料庫持久化邏輯封裝成可由建構子注入的協作者，讓測試可傳入記憶體假資料庫。
- 將欄位驗證（例如 `event` 必填）提取成輔助函式，使控制器更簡潔。【F:release/app/api/controllers.py†L95-L169】

### `app/streaming/` 套件
- `window_finder.py`：負責列舉視窗與依據程序名稱篩選，供單一視窗搜尋與可用程式清單共用。【F:release/app/api/controllers.py†L200-L265】【F:release/app/api/controllers.py†L604-L707】
- `capture.py`：包含 `_capture_desktop` 與 `_capture_normal_window`，以依賴注入方式（如傳入 `win32gui`, `win32ui`）實作，方便測試。針對 `yuanshen.exe` 的遮罩計算應獨立處理，以便其他遊戲套用不同遮罩。【F:release/app/api/controllers.py†L267-L482】
- `streamer.py`：專注於串流狀態機（`generate_frames`、`start_stream`、`stop_stream`），並將畫面擷取與視窗搜尋交由其他模組。Flask 只需連接這些簡潔的 API。【F:release/app/api/controllers.py†L484-L582】
- `programs.py`：基於 finder 實作「可用程式清單」，回傳去重且已篩選的名稱。【F:release/app/api/controllers.py†L604-L707】

### `app/controllers/system_info.py`
- 保留 `SystemInfoController`，並額外公開 `get_cpu_usage`、`get_memory_usage` 等函式，讓測試可傳入類似 `psutil` 的模擬物件。【F:release/app/api/controllers.py†L715-L782】

## 依賴注入與隔離
- 透過建構子傳入輕量介面（protocol 或 callable），讓測試能注入假物件：
  - `WindowFinder`：提供 `find(process_name)` 與 `list()`，供串流與程式清單端點使用。【F:release/app/api/controllers.py†L200-L265】【F:release/app/api/controllers.py†L604-L707】
  - `FrameCapture`：提供 `capture(hwnd)` 回傳 `np.ndarray`，封裝畫面來源（桌面或視窗）。【F:release/app/api/controllers.py†L267-L482】
  - `SystemMetrics`：提供 `memory_percent()` 與 `cpu_percent(interval)`，讓控制器僅負責格式化。【F:release/app/api/controllers.py†L735-L775】
- 將全域狀態（如 `self.hwnd`、`self.is_streaming`）封裝在一個小型「串流會話」物件中，並讓該物件管理生成器生命週期，方便測試。【F:release/app/api/controllers.py†L484-L570】

## 測試策略

### 單元測試（mock / stub）
- 用 `pytest` 測試 `LogController` 的 log 反轉與例外處理，模擬會拋出錯誤的假 `LogDataManager`。【F:release/app/api/controllers.py†L49-L86】
- 對 `WebhookController` 傳入假資料庫，驗證錯誤與成功情境能回傳正確字典，無需觸及 SQLite。【F:release/app/api/controllers.py†L116-L169】
- 測試遮罩計算邏輯時，傳入固定視窗大小並驗證結果是否正確（先將計算邏輯抽成純函式）。【F:release/app/api/controllers.py†L433-L470】

### 整合式測試（依賴注入）
- 建立記憶體版 `FrameCapture` 假物件，讓串流生成器能在不調用 Win32 API 下執行。【F:release/app/api/controllers.py†L484-L570】
- 模擬視窗列舉流程，使 finder 回傳一系列假 handle，用以測試「視窗遺失並重試」的路徑。【F:release/app/api/controllers.py†L529-L544】

### Flask 端點的契約／驗收測試
- 將重構後的控制器掛載到 Flask blueprint，使用 `FlaskClient` 驗證 JSON 回應與串流端點。由於依賴可注入假物件，測試能跨平台並適合 CI 執行。

## 漸進式重構步驟
1. 先把 `SystemInfoController` 拆出到獨立模組，風險最低。
2. 抽出共用視窗列舉邏輯成 `window_utils.py`，供 `find_window_by_process_name` 與 `get_available_programs` 共用。
3. 將 `StreamController` 的 `win32*` 依賴改為注入式 adapter，並將 `_capture_desktop`、`_capture_normal_window` 移入其中。
4. 在依賴面積縮小後，再將各控制器分檔，並更新 Flask import。
5. 使用 `pytest` 撰寫假管理器與關鍵功能的測試，以確保行為一致。

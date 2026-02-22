# Auto-Typing 語音打字小幫手 🎙️⌨️

這是一個基於 Python 與 Google Gemini API 打造的 Windows 常駐型「語音轉文字自動打字」工具。
透過簡單的快捷鍵操作，你可以直接用說話的方式將文字輸入到任何支援游標的視窗（例如：Word、Line、瀏覽器等）。

---

## ✨ 功能特色

- **一鍵語音輸入**：長按 `Esc` 鍵開始錄音，放開即自動將語音轉換為文字並自動輸入到當前視窗。
- **螢幕提示 (OSD)**：錄音、處理中、成功或失敗等狀態皆會有直覺的螢幕浮動文字提示（On-Screen Display），讓您清楚當下動作。
- **系統匣常駐**：啟動後會隱藏於右下角系統匣中，不佔用工具列空間，背景默默為您服務。
- **高精準度辨識**：串接 Google Gemini API 進行語音轉錄（Speech-to-Text），支援自然語言處理與優良的辨識準確度。
- **防誤觸設計**：長按快捷鍵（>= 0.5 秒）才會啟動錄音，避免與一般日常按鍵操作衝突。

---

## 🛠️ 安裝與設定說明

### 系統需求
- 作業系統：Windows 10 / 11
- Python 3.9+ (若自行從原始碼執行)

### 1. 取得專案原始碼
```bash
git clone https://github.com/smallken99/voice-auto-typer.git
cd voice-auto-typer
```

### 2. 安裝依賴套件 (Python 環境)
建議使用虛擬環境 (Virtual Environment)：
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 設定 API Key
本專案的自動潤稿功能依賴 Google Gemini API，請先取得您專屬的 `GEMINI_API_KEY`。

**如何取得 Gemini API Key：**
1. 前往 [Google AI Studio](https://aistudio.google.com/app/apikey) 並登入您的 Google 帳號。
2. 點擊「Create API key」按鈕，建立一組專屬的 API 金鑰並複製起來。

**套用金鑰：**
1. 將根目錄的 `.env.example` 重新命名為 `.env`。
2. 編輯 `.env` 檔案，將您的 API Key 填入：
```env
GEMINI_API_KEY=你的_GEMINI_API_KEY_放在這裡
```

---

## 🚀 如何使用

### 執行方式
在專案根目錄下，執行主程式：
```bash
python main.py
```

若您已經將程式打包 (或者下載了已經打包好的版本)，可以直接執行 `Auto-Typing.exe`。

### 操作步驟
1. 程式啟動後，螢幕會短暫出現「🚀 語音助手已啟動，長按 Esc 說話」的提示，並在右下角系統匣產生一個綠色小方塊圖示。
2. 將游標點擊到您想要輸入文字的任何地方（例如記事本、Line 聊天框）。
3. **按住 `Esc` 鍵**（超過 0.5 秒），螢幕會顯示「🔴 錄音中...」，此時請開始說話。
4. **放開 `Esc` 鍵**，螢幕會顯示「⏳ AI 處理中...」，程式會自動將錄音檔送至 Gemini 進行轉錄。
5. 轉換完成後，文字會**自動貼上**到您的游標位置，並顯示「✅ 貼上完成」。

### 如何關閉
在右下角系統匣找到綠色方塊圖示，點擊右鍵並選擇「退出 (Exit)」即可完全關閉程式。

---

## 📦 打包發布 (建置 EXE)

如果你希望將此程式打包為單一的可執行檔，可以透過 `PyInstaller`：
```bash
pyinstaller Auto-Typing.spec
```
建置完成後，即可在 `dist/` 資料夾中找到打包好的 `Auto-Typing.exe`！

---

## 📁 專案架構

- `main.py`: 主程式進入點，處理快捷鍵監聽、系統匣圖示等主要邏輯。
- `audio_recorder.py`: 負責處理麥克風聲音的錄製與儲存 (`sounddevice`, `soundfile`)。
- `gemini_api.py`: 負責與 Google Gemini API 溝通，上傳音源並取得轉錄文字。
- `clipboard_typer.py`: 負責讀取文字並模擬鍵盤貼上動作 (`pyperclip`, `pyautogui`)。
- `osd_ui.py`: 提供畫面上的無邊框浮動提示文字 UI。
- `Auto-Typing.spec`: PyInstaller 的打包設定檔。

---

## 📜 授權條款
本專案依據 MIT License 開源，歡迎自由修改與使用。

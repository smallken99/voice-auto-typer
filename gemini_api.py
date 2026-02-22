import os
import sys
import tkinter as tk
from tkinter import messagebox
from google import genai
from dotenv import load_dotenv

# 取得目前程式執行的絕對路徑 (若被 pyinstaller 打包，為 exe 所在位置)
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

# 載入與主程式同層的 .env 環境變數
env_path = os.path.join(app_path, ".env")
load_dotenv(dotenv_path=env_path)

# 設定 Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "你的_GEMINI_API_KEY_放在這裡":
    print("❌ 請確保 .env 檔案中的 GEMINI_API_KEY 已經正確設定！")
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("錯誤", "找不到 .env 檔案或 GEMINI_API_KEY 未設定！\n請確保 .env 檔案放在與執行檔 (exe) 相同的資料夾中！")
    sys.exit(1)

# 初始化新版 Gemini 客戶端
client = genai.Client(api_key=api_key)

def refine_text(raw_text: str):
    """
    將初版轉錄文字傳遞給 Gemini 進行潤稿與修正
    """
    if not raw_text or not raw_text.strip():
        print("❌ 沒有提供可以潤稿的文字。")
        return None

    try:
        print("⏳ 正在將文字交由 Gemini 潤稿 ...")
        
        # 準備 Prompt (依照需求定義)
        prompt = (
            "這是一段由語音辨識系統轉錄的草稿文字：\n"
            f"「{raw_text}」\n\n"
            "請對上述文字進行潤稿處理。請：\n"
            "1. 自動加上適當的標點符號。\n"
            "2. 修正明顯的錯別字或語音辨識錯誤。\n"
            "3. 移除『嗯』、『那個』、『對』等無意義的贅字與口語停頓。\n"
            "4. 保持講者原本的意思與語氣，不要擅自擴寫或總結。\n"
            "5. 請『只』輸出最終的繁體中文文字結果，不要包含任何其他解釋或引言。"
        )
        
        # 向模型發送請求
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # 回傳純文字結果
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Gemini 潤稿時發生錯誤: {e}")
        return raw_text # 倘若失敗，至少退回原始的轉錄文字

if __name__ == "__main__":
    # 測試用
    print("開始測試 Gemini 文字潤稿...")
    test_raw_text = "我我那個想說，今天天氣不錯，嗯，我們去打球吧對啊。"
    result_text = refine_text(test_raw_text)
    if result_text:
        print("\n--- 潤稿結果 ---")
        print(result_text)
        print("----------------\n")

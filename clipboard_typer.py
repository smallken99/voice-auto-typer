import pyperclip
import pyautogui
import time

def auto_type_text(text):
    """
    將文字複製到系統剪貼簿，然後模擬 Ctrl+V 貼上
    """
    if not text:
        return
        
    try:
        # 1. 將文字放入剪貼簿
        pyperclip.copy(text)
        
        # 2. 為了確保作業系統與目標應用程式有足夠時間接收剪貼簿變更，稍微等待一下
        time.sleep(0.1)
        
        # 3. 模擬按下 Ctrl + V
        pyautogui.hotkey('ctrl', 'v')
        
    except Exception as e:
        print(f"❌ 自動貼上文字時發生錯誤: {e}")

if __name__ == "__main__":
    # 測試用：請在 3 秒內將游標點擊到任何可以輸入文字的地方（例如記事本或這裡的終端機）
    print("準備測試自動打字！請在 3 秒內將滑鼠游標點擊到可以輸入文字的地方...")
    for i in range(3, 0, -1):
        print(f"倒數 {i} 秒...")
        time.sleep(1)
        
    test_text = "這是一段從剪貼簿自動貼上的測試文字！"
    print(f"正在貼上: {test_text}")
    auto_type_text(test_text)
    print("✅ 測試完成！請檢查上面或你點擊的視窗是否有出現文字。")

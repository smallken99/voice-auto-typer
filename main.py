import keyboard
import time
import threading
import sys
import os
import multiprocessing
import tkinter as tk

# 匯入系統匣圖示套件
import pystray
from PIL import Image, ImageDraw

# 匯入我們自己寫的模組
from audio_recorder import AudioRecorder
from local_whisper import transcribe_audio_local, init_model
from gemini_api import refine_text
from clipboard_typer import auto_type_text
from osd_ui import OSD

osd = OSD()

def process_audio(recorder):
    """
    這是一個在背景執行的函數，用來處理語音並貼上文字。
    這樣主迴圈就不會被停頓，能繼續監聽下一次按鍵。
    """
    osd.show_text("⏳ 語音轉錄中...", "#ffff00") # 黃色
    print("\n⏳ 正在使用本地 Whisper 轉錄語音，請稍候...")
    raw_text = transcribe_audio_local(recorder.filename)
    
    if raw_text:
        print(f"✅ 初步轉錄結果: {raw_text}")
        osd.show_text("⏳ AI 潤稿中...", "#ffff00") # 黃色
        print("⏳ 正在將文字送往 Gemini 進行潤稿，請稍候...")
        
        refined_text = refine_text(raw_text)
        
        if refined_text:
            print(f"✨ 最終潤稿結果: {refined_text}")
            auto_type_text(refined_text)
            print("✅ 已經自動為您貼上文字囉！")
            osd.show_text("✅ 貼上完成", "#00ffff") # 青色
            time.sleep(1.5)
            osd.hide()
        else:
            print("❌ 無法取得潤稿結果。")
            osd.show_text("❌ 潤稿失敗", "#ff0000") # 紅色
            time.sleep(2)
            osd.hide() 
    else:
        print("❌ 無法取得轉錄結果。")
        osd.show_text("❌ 處理失敗", "#ff0000") # 紅色
        time.sleep(2)
        osd.hide() 

def create_image():
    """ 產生一個簡單的正方形圖示，作為系統匣圖示使用 """
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    d = ImageDraw.Draw(image)
    d.rectangle([(16, 16), (48, 48)], fill=(0, 200, 0)) # 綠色小方塊
    return image

def show_splash_and_load_model():
    """ 
    顯示 Tkinter 啟動畫面，並在背景載入模型。
    載入完成後會關閉此視窗。
    """
    splash = tk.Tk()
    splash.overrideredirect(True) # 隱藏標題列邊框
    
    # 設定視窗置中
    window_width = 400
    window_height = 150
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    splash.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
    
    splash.configure(bg="#2d2d2d")
    
    label_title = tk.Label(splash, text="🚀 語音助手啟動中...", font=("Microsoft JhengHei", 14, "bold"), bg="#2d2d2d", fg="white")
    label_title.pack(pady=(30, 10))
    
    label_info = tk.Label(splash, text="正在載入語音加速模型，初次執行將自動下載。\n下載過程可能需要數分鐘，請您耐心等候...", font=("Microsoft JhengHei", 10), bg="#2d2d2d", fg="#aaaaaa")
    label_info.pack()

    def _load_model_thread():
        try:
            init_model()
        except Exception as e:
            print(f"啟動時載入模型發生錯誤: {e}")
        finally:
            # 載入完成，關閉 splash 畫面
            splash.after(0, splash.destroy)

    # 啟動背景執行緒載入模型，以避免卡死 UI
    threading.Thread(target=_load_model_thread, daemon=True).start()
    
    # 阻塞直到 splash 被 destroy
    splash.mainloop()

def main():
    # 步驟 1：顯示啟動畫面並初始化模型
    # 這會阻擋主程式直到模型載入完畢（或下載完畢）
    show_splash_and_load_model()
    
    # 步驟 2：正式進入系統後台準備
    recorder = AudioRecorder("temp_audio.wav")
    hotkey = 'esc'
    
    # 控制背景執行緒的開關
    stop_event = threading.Event()
    
    def keyboard_listener():
        is_pressed = False
        press_start_time = 0
        recording_started = False
        
        try:
            while not stop_event.is_set():
                # 偵測快捷鍵是否被按下
                if keyboard.is_pressed(hotkey):
                    if not is_pressed:
                        # 剛剛按下，開始計時
                        is_pressed = True
                        press_start_time = time.time()
                    elif not recording_started and (time.time() - press_start_time) >= 0.5:
                        # 按住超過 0.5 秒，並且還沒開始錄音 -> 啟動錄音
                        recording_started = True
                        osd.show_text("🔴 錄音中...", "#00ff00") # 綠色
                        recorder.start_recording()
                else:
                    # 放開按鍵
                    if is_pressed:
                        is_pressed = False
                        if recording_started:
                            # 之前有成功啟動錄音，才停止並處理
                            recording_started = False
                            osd.hide()
                            recorder.stop_recording()
                            
                            # 使用 Thread 來避免阻塞
                            processing_thread = threading.Thread(target=process_audio, args=(recorder,))
                            processing_thread.start()
                        # 否則 (按不到 0.5 秒) 就什麼都不做，當作一般案件發生
                        
                time.sleep(0.01) # 稍微暫停以避免 CPU 使用率過高
        except Exception as e:
            print(f"鍵盤監聽發生錯誤: {e}")
        finally:
            if recorder.recording:
                recorder.stop_recording()

    # 將快捷鍵監聽放入背景執行緒，以免卡住系統匣的 UI 執行緒
    listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
    listener_thread.start()

    # 系統匣結束操作
    def on_quit(icon, item):
        print("正在關閉程式...")
        stop_event.set()
        icon.stop()

    print("\n" + "=" * 50)
    print("🎙️ Auto-Typing 語音打字小幫手已啟動！(常駐系統匣模式)")
    print(f"👉 請「按住」 'Esc' 鍵開始說話，放開即進入自動處理...")
    print("👉 請在螢幕右下角系統匣角落找到綠色方塊圖示，右鍵即可「退出 (Exit)」。")
    print("=" * 50 + "\n")

    # 顯示啟動成功的提示
    def show_startup_message():
        osd.show_text("🚀 語音助手已啟動，長按 Esc 說話", "#00ffff") # 青藍色
        time.sleep(3)
        osd.hide()
    
    threading.Thread(target=show_startup_message, daemon=True).start()

    # 建立與執行系統匣圖示 (會阻塞在這裡直到 icon.stop() 被呼叫)
    menu = pystray.Menu(pystray.MenuItem('退出 (Exit)', on_quit))
    icon = pystray.Icon("Auto-Typing", create_image(), "Auto-Typing 語音助手", menu)
    icon.run()

if __name__ == '__main__':
    # 解決 Pyinstaller 打包後 faster-whisper/ctranslate2 產生的 multiprocess 無窮迴圈問題
    multiprocessing.freeze_support()
    main()

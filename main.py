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

def process_audio_raw(recorder):
    """
    快速模式：語音轉錄後直接貼上，不經過 Gemini 潤稿。
    """
    osd.show_text("⏳ 快速轉錄中...", "#ffa500") # 橘色
    print("\n⏳ [快速模式] 正在使用本地 Whisper 轉錄語音，請稍候...")
    raw_text = transcribe_audio_local(recorder.filename)
    
    if raw_text:
        print(f"✅ [快速模式] 轉錄結果: {raw_text}")
        auto_type_text(raw_text)
        print("✅ [快速模式] 已直接貼上原始轉錄文字！")
        osd.show_text("✅ 快速貼上完成", "#00ffff") # 青色
        time.sleep(1.5)
        osd.hide()
    else:
        print("❌ [快速模式] 無法取得轉錄結果。")
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
    hotkey = 'right alt'
    
    # 控制背景執行緒的開關
    stop_event = threading.Event()
    
    def keyboard_listener():
        # 右 Alt 鍵（Gemini 潤稿模式）狀態
        esc_is_pressed = False
        esc_press_start_time = 0
        esc_recording_started = False
        
        # Caps Lock 鍵（快速模式）狀態
        caps_is_pressed = False
        caps_press_start_time = 0
        caps_recording_started = False
        
        try:
            while not stop_event.is_set():
                any_recording = esc_recording_started or caps_recording_started
                
                # ===== 右 Alt 鍵（Gemini 潤稿模式）=====
                if keyboard.is_pressed(hotkey):
                    if not esc_is_pressed:
                        esc_is_pressed = True
                        esc_press_start_time = time.time()
                    elif not esc_recording_started and not any_recording and (time.time() - esc_press_start_time) >= 0.5:
                        esc_recording_started = True
                        osd.show_text("🔴 錄音中...", "#00ff00") # 綠色
                        recorder.start_recording()
                else:
                    if esc_is_pressed:
                        esc_is_pressed = False
                        if esc_recording_started:
                            esc_recording_started = False
                            osd.hide()
                            recorder.stop_recording()
                            processing_thread = threading.Thread(target=process_audio, args=(recorder,))
                            processing_thread.start()
                
                # ===== Caps Lock 鍵（快速模式，跳過潤稿）=====
                if keyboard.is_pressed('caps lock'):
                    if not caps_is_pressed:
                        caps_is_pressed = True
                        caps_press_start_time = time.time()
                    elif not caps_recording_started and not any_recording and (time.time() - caps_press_start_time) >= 0.5:
                        caps_recording_started = True
                        osd.show_text("🔴 快速錄音中...", "#ffa500") # 橘色
                        recorder.start_recording()
                else:
                    if caps_is_pressed:
                        caps_is_pressed = False
                        if caps_recording_started:
                            caps_recording_started = False
                            osd.hide()
                            recorder.stop_recording()
                            processing_thread = threading.Thread(target=process_audio_raw, args=(recorder,))
                            processing_thread.start()
                
                time.sleep(0.01) # 稍微暫停以避免 CPU 使用率過高
        except Exception as e:
            print(f"鍵盤監聽發生錯誤: {e}")
        finally:
            if recorder.recording:
                recorder.stop_recording()

    # 將快捷鍵監聽放入背景執行緒，以免卡住系統匣的 UI 執行緒
    listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
    listener_thread.start()

    # 系統匣說明視窗
    def on_help(icon, item):
        def _show_help():
            win = tk.Tk()
            win.title("🎙️ 語音助手 - 操作說明")
            win.configure(bg="#1e1e2e")
            win.resizable(False, False)

            # 視窗置中
            win_w, win_h = 400, 300
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            win.geometry(f"{win_w}x{win_h}+{(sw-win_w)//2}+{(sh-win_h)//2}")

            tk.Label(win, text="🎙️ 語音助手 操作說明",
                     font=("Microsoft JhengHei", 13, "bold"),
                     bg="#1e1e2e", fg="#cba6f7").pack(pady=(18, 8))

            help_items = [
                ("右 Alt（按住 0.5 秒後說話）", "🟢 潤稿模式  →  Whisper 轉錄 + Gemini 潤稿後貼上"),
                ("Caps Lock（按住 0.5 秒後說話）", "🟠 快速模式  →  Whisper 轉錄後直接貼上，不潤稿"),
                ("放開按鍵", "⏹  停止錄音並開始處理"),
            ]

            frame = tk.Frame(win, bg="#181825", bd=0)
            frame.pack(fill="both", padx=20, pady=4, expand=True)

            for hotkey_name, desc in help_items:
                row = tk.Frame(frame, bg="#181825")
                row.pack(fill="x", pady=6, padx=12)
                tk.Label(row, text=hotkey_name,
                         font=("Microsoft JhengHei", 10, "bold"),
                         bg="#181825", fg="#89dceb", anchor="w").pack(anchor="w")
                tk.Label(row, text=desc,
                         font=("Microsoft JhengHei", 9),
                         bg="#181825", fg="#cdd6f4", anchor="w").pack(anchor="w")

            tk.Button(win, text="關閉", command=win.destroy,
                      font=("Microsoft JhengHei", 10),
                      bg="#313244", fg="white", relief="flat",
                      activebackground="#45475a", activeforeground="white",
                      cursor="hand2", padx=20, pady=4).pack(pady=12)

            win.mainloop()

        threading.Thread(target=_show_help, daemon=True).start()

    # 系統匣結束操作
    def on_quit(icon, item):
        print("正在關閉程式...")
        stop_event.set()
        icon.stop()

    print("\n" + "=" * 50)
    print("🎙️ Auto-Typing 語音打字小幫手已啟動！(常駐系統匣模式)")
    print(f"👉 請「按住」右邊的 'Alt' 鍵開始說話，放開即進入自動處理（含 AI 潤稿）...")
    print(f"👉 請「按住」 'Caps Lock' 鍵開始說話，放開即快速貼上（不經潤稿）...")
    print("👉 請在螢幕右下角系統匣角落找到綠色方塊圖示，右鍵即可「退出 (Exit)」。")
    print("=" * 50 + "\n")

    # 顯示啟動成功的提示
    def show_startup_message():
        osd.show_text("🚀 語音助手已啟動｜右Alt: 潤稿｜CapsLock: 快速", "#00ffff") # 青藍色
        time.sleep(3)
        osd.hide()
    
    threading.Thread(target=show_startup_message, daemon=True).start()

    # 建立與執行系統匣圖示 (會阻塞在這裡直到 icon.stop() 被呼叫)
    menu = pystray.Menu(
        pystray.MenuItem('說明 (Help)', on_help),
        pystray.MenuItem('退出 (Exit)', on_quit),
    )
    icon = pystray.Icon("Auto-Typing", create_image(), "Auto-Typing 語音助手", menu)
    icon.run()

if __name__ == '__main__':
    # 解決 Pyinstaller 打包後 faster-whisper/ctranslate2 產生的 multiprocess 無窮迴圈問題
    multiprocessing.freeze_support()
    main()

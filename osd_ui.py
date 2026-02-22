import tkinter as tk
import queue
import threading

class OSD(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.q = queue.Queue()
        self.start()

    def run(self):
        # 建立 Tkinter 根視窗 (跑在獨立執行緒)
        self.root = tk.Tk()
        self.root.overrideredirect(True) # 無邊框
        self.root.attributes('-topmost', True) # 最上層顯示
        self.root.attributes('-disabled', True) # 忽略滑鼠點擊 (穿透點擊)
        self.root.attributes('-alpha', 0.85) # 微透明
        
        # 視窗樣式設定
        bg_color = '#222222'
        self.root.configure(bg=bg_color)
        
        self.label = tk.Label(self.root, text="", font=('微軟正黑體', 18, 'bold'),
                              fg='#00ff00', bg=bg_color, padx=20, pady=10)
        self.label.pack(expand=True, fill='both')
        self.root.withdraw() # 初始隱藏
        
        self.check_queue()
        self.root.mainloop()
        
    def _center_window(self):
        # 動態置中於畫面正下方
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_reqwidth()
        window_height = self.root.winfo_reqheight()
        
        x = (screen_width // 2) - (window_width // 2)
        y = screen_height - 180 # 底部往上
        self.root.geometry(f"+{x}+{y}")

    def check_queue(self):
        """定期檢查來自其他執行緒的顯示需求"""
        try:
            while True:
                msg = self.q.get_nowait()
                if msg == "HIDE":
                    self.root.withdraw()
                else:
                    text, color = msg
                    self.label.config(text=text, fg=color)
                    self._center_window()
                    self.root.deiconify()
        except queue.Empty:
            pass
        self.root.after(50, self.check_queue)
        
    def show_text(self, text, color='#00ff00'):
        """執行緒安全的顯示文字方法"""
        self.q.put((text, color))
        
    def hide(self):
        """執行緒安全的隱藏視窗方法"""
        self.q.put("HIDE")

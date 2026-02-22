import keyboard
import sounddevice as sd
import soundfile as sf
import queue
import threading
import sys
import time

class AudioRecorder:
    def __init__(self, filename="temp_audio.wav", samplerate=44100, channels=1):
        self.filename = filename
        self.samplerate = samplerate
        self.channels = channels
        self.q = queue.Queue()
        self.recording = False
        self.stream = None
        self.thread = None

    def callback(self, indata, frames, time, status):
        """此回呼函式會在另一個執行緒中被呼叫，用來處理每一塊音訊資料"""
        if status:
            print(f"錄音狀態: {status}", file=sys.stderr)
        if self.recording:
            # 將收到的音訊資料放入佇列
            self.q.put(indata.copy())

    def _file_writing_thread(self):
        """將佇列中的音訊資料寫入硬碟的背景執行緒"""
        try:
            with sf.SoundFile(self.filename, mode='w', samplerate=self.samplerate, channels=self.channels) as file:
                while self.recording or not self.q.empty():
                    try:
                        data = self.q.get(timeout=0.1)
                        file.write(data)
                    except queue.Empty:
                        continue
        except Exception as e:
            print(f"寫入檔案時發生錯誤: {e}")

    def start_recording(self):
        """開始錄音"""
        if self.recording:
            return
            
        self.recording = True
        self.q = queue.Queue() # 清空先前的佇列
        
        print("🔴 開始錄音...")
        
        try:
            self.stream = sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=self.callback)
            self.stream.start()
            
            # 啟動寫入檔案的執行緒
            self.thread = threading.Thread(target=self._file_writing_thread)
            self.thread.start()
        except Exception as e:
            print(f"啟動錄音失敗: {e}")
            self.recording = False

    def stop_recording(self):
        """停止錄音"""
        if not self.recording:
            return
            
        self.recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        # 等待檔案寫入完成
        if self.thread:
            self.thread.join()
            self.thread = None
            
        print(f"⏹ 結束錄音，已儲存至 {self.filename}")

def main():
    recorder = AudioRecorder("temp_audio.wav")
    hotkey = 'ctrl'
    is_pressed = False
    
    print(f"準備就緒！請「按住」 {hotkey} 鍵開始說話，放開即停止錄音...")
    print("按下 'Esc' 鍵可結束測試程式。")
    
    try:
        while True:
            # 提供一個跳出的方式
            if keyboard.is_pressed('esc'):
                print("測試程式結束。")
                break
                
            # 偵測快捷鍵是否被按下
            if keyboard.is_pressed(hotkey):
                if not is_pressed:
                    is_pressed = True
                    recorder.start_recording()
            else:
                if is_pressed:
                    is_pressed = False
                    recorder.stop_recording()
                    
            time.sleep(0.05) # 稍微暫停以避免 CPU 使用率過高
    except KeyboardInterrupt:
        print("\n程式被強制中斷。")
    finally:
        # 確保程式結束時會關閉錄音
        if recorder.recording:
            recorder.stop_recording()

if __name__ == '__main__':
    main()

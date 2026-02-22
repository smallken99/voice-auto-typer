import os

# 隱藏在 Windows 上因為不支援符號連結 (symlinks) 而產生的警告
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import sys
from faster_whisper import WhisperModel

# 全域模型變數
model = None

def init_model(model_size="small"):
    """
    初始化模型。首次呼叫時會自動下載模型權重到本地 models 資料夾。
    """
    global model
    if model is not None:
        return # 已經載入過就不要重複載入

    # 取得目前程式執行的絕對路徑 (若被 pyinstaller 打包，為 exe 所在位置)
    if getattr(sys, 'frozen', False):
        app_path = os.path.dirname(sys.executable)
    else:
        app_path = os.path.dirname(os.path.abspath(__file__))

    models_dir = os.path.join(app_path, "models")
    os.makedirs(models_dir, exist_ok=True)

    try:
        print(f"⏳ 正在載入 faster-whisper 模型 ({model_size}) 至 {models_dir} ...")
        # 可以根據硬體效能選擇 "base", "small", 或 "medium"
        # 若有支援 CUDA，可以將 device="cuda", compute_type="float16" 以加速
        model = WhisperModel(model_size, device="cpu", compute_type="int8", download_root=models_dir)
    except Exception as e:
        print(f"⚠️ 載入模型時遭遇問題，改用基礎設定重新嘗試: {e}")
        try:
            model = WhisperModel("base", device="cpu", compute_type="int8", download_root=models_dir)
        except Exception as inner_e:
            print(f"❌ 嚴重錯誤，無法載入任何模型: {inner_e}")

def transcribe_audio_local(audio_path="temp_audio.wav"):
    """
    使用本地端 faster-whisper 將音訊即時轉錄為純文字。
    回傳繁體中文文字字串。
    """
    # 確保模型已經載入
    if model is None:
        init_model()

    if not os.path.exists(audio_path):
        print(f"❌ 找不到音訊檔案: {audio_path}")
        return None

    try:
        print(f"⏳ 本地 Whisper 正在轉錄音訊: {audio_path} ...")
        
        # 進行轉錄，強制語言為繁體中文 (zh)
        segments, info = model.transcribe(audio_path, beam_size=5, language="zh")
        
        # 組合所有轉錄片段的文字
        text_result = []
        for segment in segments:
            text_result.append(segment.text)
            
        final_text = "".join(text_result).strip()
        return final_text
        
    except Exception as e:
        print(f"❌ 本地轉錄時發生錯誤: {e}")
        return None

if __name__ == "__main__":
    # 單獨測試 local_whisper
    test_file = "temp_audio.wav"
    result = transcribe_audio_local(test_file)
    print("\n--- 本地 Whisper 轉錄結果 ---")
    print(result)
    print("--------------------------------\n")

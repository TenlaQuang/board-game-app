import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import base64
import pygame
import time # [THÊM] Để đo thời gian thực

class AudioManager:
    def __init__(self):
        self.sample_rate = 16000  
        self.channels = 1
        self.recording = None
        self.is_recording = False
        self.start_time = 0 # [THÊM] Biến lưu thời điểm bắt đầu
        
        try:
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
        except: pass

        self.temp_dir = "temp_audio"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def start_recording(self):
        self.is_recording = True
        self.start_time = time.time() # [THÊM] Bấm giờ
        # Thu sẵn 10s (nhưng tí nữa sẽ cắt)
        self.recording = sd.rec(int(10 * self.sample_rate), samplerate=self.sample_rate, channels=self.channels)

    def stop_recording(self, filename="my_voice.wav"):
        if not self.is_recording: return None
        
        self.is_recording = False
        sd.stop()
        
        # [QUAN TRỌNG: CẮT FILE]
        # 1. Tính thời gian thực tế đã thu (VD: 0.6s)
        elapsed_time = time.time() - self.start_time
        
        # 2. Tính số lượng mẫu (Samples) cần lấy
        valid_samples = int(elapsed_time * self.sample_rate)
        
        # 3. Cắt mảng dữ liệu (Chỉ lấy phần có tiếng, vứt phần 10s thừa đi)
        # self.recording là mảng to, ta cắt lấy [0 : valid_samples]
        actual_audio = self.recording[:valid_samples]
        
        # [XỬ LÝ LỖI NaN]
        actual_audio = np.nan_to_num(actual_audio)

        # [TÍNH NĂNG MỚI: TỰ ĐỘNG TĂNG ÂM LƯỢNG (NORMALIZE)]
        # Nếu bạn hét mà volume chỉ 16 là quá bé. Code này sẽ kích âm lên to nhất có thể.
        max_val = np.max(np.abs(actual_audio))
        if max_val > 0:
            # Khuếch đại sao cho đỉnh cao nhất chạm mốc 0.9 (gần max loa)
            actual_audio = actual_audio / max_val * 0.9
            print(f"DEBUG: Đã khuếch đại âm thanh (Gốc: {max_val:.4f})")
        
        # Chuyển sang INT16 để lưu file
        audio_int16 = (actual_audio * 32767).astype(np.int16)
        
        filepath = os.path.join(self.temp_dir, filename)
        wav.write(filepath, self.sample_rate, audio_int16)
        
        # In ra dung lượng file để kiểm tra (Nó phải nhỏ, tầm 20KB thôi)
        file_size = os.path.getsize(filepath)
        print(f"DEBUG: File ghi âm dài {elapsed_time:.1f}s - Kích thước: {file_size/1024:.1f} KB")
        
        return filepath

    def audio_to_string(self, filepath):
        if not os.path.exists(filepath): return ""
        with open(filepath, "rb") as f:
            audio_bytes = f.read()
        return base64.b64encode(audio_bytes).decode('utf-8')

    def string_to_audio(self, b64_string, filename):
        filepath = os.path.join(self.temp_dir, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(b64_string))
            return filepath
        except Exception as e:
            print(f"Lỗi giải mã audio: {e}")
            return None

    def play_sound(self, filepath):
        try:
            if os.path.exists(filepath):
                sound = pygame.mixer.Sound(filepath)
                sound.set_volume(1.0) 
                sound.play()
                print(f"Đang phát: {filepath}")
            else:
                print("File không tồn tại!")
        except Exception as e:
            print(f"Lỗi phát âm thanh: {e}")
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import base64
import pygame

class AudioManager:
    def __init__(self):
        # [SỬA 1] Giảm chất lượng xuống để nhẹ mạng (8000Hz là chuẩn thoại điện thoại)
        self.sample_rate = 16000  
        self.channels = 1
        self.recording = None
        self.is_recording = False
        
        # [SỬA 2] Khởi tạo Mixer của Pygame ngay khi tạo Manager
        try:
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
        except: pass

        self.temp_dir = "temp_audio"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        # [DEBUG] In ra danh sách thiết bị để xem máy đang dùng Mic nào
        print("\n--- DANH SÁCH THIẾT BỊ ÂM THANH ---")
        print(sd.query_devices())
        print("-----------------------------------\n")

    def start_recording(self):
        self.is_recording = True
        # Thu âm với định dạng float32 (mặc định)
        self.recording = sd.rec(int(10 * self.sample_rate), samplerate=self.sample_rate, channels=self.channels)

    def stop_recording(self, filename="my_voice.wav"):
        if not self.is_recording: return None
        
        self.is_recording = False
        sd.stop()
        
        # Cắt bỏ phần thừa (lấy độ dài thực tế)
        # Vì sd.rec chạy non-blocking, ta cần wait để đảm bảo dữ liệu về đủ
        # Nhưng ở đây ta đã bấm nút Stop rồi nên sd.stop() đã xử lý.
        
        # [SỬA 3] Kiểm tra xem có tiếng không (hay toàn im lặng)
        volume_norm = np.linalg.norm(self.recording) * 10
        print(f"DEBUG: Độ lớn âm thanh thu được: {int(volume_norm)}")
        
        if volume_norm < 1:
            print("⚠ CẢNH BÁO: Không thu được tiếng gì cả (Micro lỗi hoặc chưa chọn đúng)")

        filepath = os.path.join(self.temp_dir, filename)
        
        # [QUAN TRỌNG] Chuyển đổi sang INT16 để Pygame phát được
        # Dữ liệu gốc là float32 (-1.0 đến 1.0), nhân với 32767 để ra int16
        audio_int16 = (self.recording * 32767).astype(np.int16)
        
        wav.write(filepath, self.sample_rate, audio_int16)
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
                # Load lại file và phát
                sound = pygame.mixer.Sound(filepath)
                sound.set_volume(1.0) # Max volume
                sound.play()
                print(f"Đang phát: {filepath}")
            else:
                print("File không tồn tại!")
        except Exception as e:
            print(f"Lỗi phát âm thanh: {e}")
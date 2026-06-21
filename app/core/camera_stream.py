"""
CameraStream: đọc camera trên một thread riêng biệt, độc lập với UI thread.

Vấn đề ở bản cũ: camera.read() và AI inference đều chạy trên main thread
của Tkinter (qua self.after()), nên khi model xử lý chậm, cả cửa sổ bị đứng/giật.

Giải pháp: thread riêng liên tục đọc camera và giữ "frame mới nhất" trong bộ nhớ.
UI thread (hoặc thread xử lý AI) chỉ cần gọi get_frame() để lấy frame mới nhất,
không bao giờ bị block bởi tốc độ đọc camera.
"""
import threading
import time

import cv2


class CameraStream:
    def __init__(self, src=0, width=640, height=480, fps_target=30):
        self.src = src
        self.width = width
        self.height = height
        self.fps_target = fps_target

        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.opened_ok = False

    def start(self) -> bool:
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)  # CAP_DSHOW: mở camera nhanh hơn trên Windows
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps_target)
        # Giảm buffer để luôn lấy frame mới nhất, tránh trễ hình
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            self.opened_ok = False
            return False

        self.opened_ok = True
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        return True

    def _update_loop(self):
        delay = 1.0 / self.fps_target
        while self.running:
            t0 = time.time()
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            elapsed = time.time() - t0
            sleep_time = delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_frame(self):
        """Trả về bản copy của frame mới nhất (an toàn để xử lý/vẽ lên)."""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()
        self.frame = None
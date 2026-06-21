"""
AttendanceService: logic xác thực khuôn mặt (real + match) và ghi nhận điểm danh.
Tách hoàn toàn khỏi UI - UI chỉ gọi process_frame() và nhận kết quả để vẽ/hiển thị.
"""
import time

from app.core.anti_spoof import AntiSpoof

# Nếu giữa 2 lần xác thực "real" liên tiếp của cùng 1 người cách nhau quá
# khoảng thời gian này, coi như bị GIÁN ĐOẠN và phải xác thực lại từ đầu.
# Giá trị này phải lớn hơn rõ rệt khoảng thời gian giữa 2 lần detect liên tiếp
# (ATTENDANCE_DETECT_INTERVAL * UI_REFRESH_MS) nhưng đủ nhỏ để phát hiện
# việc "đổi nguồn" (từ mặt thật sang ảnh điện thoại của cùng người).
MAX_GAP_SECONDS = 0.5


class AttendanceService:
    def __init__(self, face_app, face_matcher, attendance_repo,
                 similarity_threshold: float, cooldown_sec: float,
                 consecutive_real_required: int = 6):
        self.face_app = face_app
        self.matcher = face_matcher
        self.attendance_repo = attendance_repo
        self.similarity_threshold = similarity_threshold
        self.cooldown_sec = cooldown_sec
        self.consecutive_real_required = consecutive_real_required

        self.session_id = None
        self.marked_ids = set()
        self._last_marked_at = {}    # student_id -> timestamp, cho phép tái chấm công sau cooldown
        self._consecutive_real = {}  # tracking_key -> số frame liên tiếp đã xác thực "real"
        self._last_real_at = {}      # tracking_key -> timestamp lần cuối xác thực "real"

    def start_session(self, session_id: int):
        self.session_id = session_id
        self.marked_ids.clear()
        self._last_marked_at.clear()
        self._consecutive_real.clear()
        self._last_real_at.clear()

    def stop_session(self):
        self.session_id = None

    def marked_count(self) -> int:
        return len(self.marked_ids)

    def process_faces(self, faces, spoof_info, bbox_scale: float = 1.0):
        """
        Với danh sách faces (từ InsightFace) và spoof_info (từ AntiSpoof),
        trả về list kết quả từng khuôn mặt để UI vẽ:
        [{'bbox': (l,t,r,b), 'label': str, 'color': (b,g,r), 'matched': bool}]

        Chỉ chấm công khi khuôn mặt đã được xác thực "real" LIÊN TỤC qua
        nhiều frame, KHÔNG GIÁN ĐOẠN quá MAX_GAP_SECONDS - chống trường hợp
        đổi từ khuôn mặt thật sang ảnh/video phát lại của CÙNG một người
        (counter cũ không được "tái sử dụng" qua khoảng gián đoạn).
        """
        results = []
        now = time.time()

        for face in faces:
            bbox = (face.bbox * bbox_scale).astype(int)
            l, t, r, b = bbox

            verified_real = False
            for real_box in spoof_info["real_boxes"]:
                if AntiSpoof.boxes_overlap((l, t, r, b), real_box):
                    verified_real = True
                    break

            if face.normed_embedding is None:
                continue

            student_id, name, similarity = self.matcher.match(face.normed_embedding)
            tracking_key = student_id if student_id else f"unknown_{l}_{t}"

            if not verified_real:
                self._consecutive_real[tracking_key] = 0
                results.append({
                    "bbox": (l, t, r, b),
                    "label": "Chưa xác thực",
                    "color": (0, 165, 255),
                    "matched": False,
                })
                continue

            # Kiểm tra GIÁN ĐOẠN thời gian: nếu lần xác thực "real" trước của
            # CHÍNH người này cách quá xa hiện tại, reset về 0 trước khi tăng.
            # Đây là lớp bảo vệ chống việc "tái sử dụng" counter đã tích lũy
            # từ lúc đứng thật, rồi sau đó đưa ảnh/video của chính người đó.
            last_real_time = self._last_real_at.get(tracking_key, 0)
            if now - last_real_time > MAX_GAP_SECONDS:
                self._consecutive_real[tracking_key] = 0

            self._last_real_at[tracking_key] = now
            count = self._consecutive_real.get(tracking_key, 0) + 1
            self._consecutive_real[tracking_key] = count

            if count < self.consecutive_real_required:
                remaining = self.consecutive_real_required - count
                results.append({
                    "bbox": (l, t, r, b),
                    "label": f"Đang xác thực... ({remaining})",
                    "color": (255, 165, 0),
                    "matched": False,
                })
                continue

            if student_id and similarity >= self.similarity_threshold:
                self._try_mark_attendance(student_id, name, similarity)
                results.append({
                    "bbox": (l, t, r, b),
                    "label": f"{name} ({similarity:.0%})",
                    "color": (34, 197, 94),
                    "matched": True,
                    "student_id": student_id,
                    "student_name": name,
                })
            else:
                results.append({
                    "bbox": (l, t, r, b),
                    "label": "Không xác định",
                    "color": (0, 165, 255),
                    "matched": False,
                })

        return results

    def _try_mark_attendance(self, student_id, name, similarity) -> bool:
        if self.session_id is None:
            return False

        now = time.time()
        last_time = self._last_marked_at.get(student_id, 0)
        if now - last_time < self.cooldown_sec:
            return False

        ok = self.attendance_repo.mark(
            session_id=self.session_id,
            student_id=student_id,
            student_name=name,
            similarity=similarity,
            status="present",
        )
        if ok:
            self.marked_ids.add(student_id)
            self._last_marked_at[student_id] = now
        return ok
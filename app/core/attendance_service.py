"""
AttendanceService: logic xác thực khuôn mặt (real + match) và ghi nhận điểm danh.
Tách hoàn toàn khỏi UI - UI chỉ gọi process_frame() và nhận kết quả để vẽ/hiển thị.
"""
import time

from app.core.anti_spoof import AntiSpoof


class AttendanceService:
    def __init__(self, face_app, face_matcher, attendance_repo,
                 similarity_threshold: float, cooldown_sec: float):
        self.face_app = face_app
        self.matcher = face_matcher
        self.attendance_repo = attendance_repo
        self.similarity_threshold = similarity_threshold
        self.cooldown_sec = cooldown_sec

        self.session_id = None
        self.marked_ids = set()
        self._last_marked_at = {}   # student_id -> timestamp, cho phép tái chấm công sau cooldown

    def start_session(self, session_id: int):
        self.session_id = session_id
        self.marked_ids.clear()
        self._last_marked_at.clear()

    def stop_session(self):
        self.session_id = None

    def marked_count(self) -> int:
        return len(self.marked_ids)

    def process_faces(self, faces, spoof_info, bbox_scale: float = 1.0):
        """
        Với danh sách faces (từ InsightFace) và spoof_info (từ AntiSpoof),
        trả về list kết quả từng khuôn mặt để UI vẽ:
        [{'bbox': (l,t,r,b), 'label': str, 'color': (b,g,r), 'matched': bool}]
        """
        results = []

        for face in faces:
            bbox = (face.bbox * bbox_scale).astype(int)
            l, t, r, b = bbox

            verified_real = False
            for real_box in spoof_info["real_boxes"]:
                if AntiSpoof.boxes_overlap((l, t, r, b), real_box):
                    verified_real = True
                    break

            if not verified_real:
                results.append({
                    "bbox": (l, t, r, b),
                    "label": "Chưa xác thực",
                    "color": (0, 165, 255),
                    "matched": False,
                })
                continue

            if face.normed_embedding is None:
                continue

            student_id, name, similarity = self.matcher.match(face.normed_embedding)

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
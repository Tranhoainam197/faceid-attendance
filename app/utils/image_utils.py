"""
Các hàm tiện ích xử lý ảnh dùng chung giữa các trang camera.
"""
import cv2
from PIL import Image, ImageTk


def bgr_to_tk_image(frame_bgr, target_size: tuple[int, int]) -> ImageTk.PhotoImage:
    """Chuyển frame OpenCV (BGR) sang ImageTk.PhotoImage để hiển thị trong CTkLabel."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)


def scale_bbox(bbox, scale: float):
    """Scale ngược bounding box (x1,y1,x2,y2) về kích thước frame gốc
    sau khi đã downscale ảnh trước khi đưa vào model detect."""
    return (bbox / scale).astype(int)
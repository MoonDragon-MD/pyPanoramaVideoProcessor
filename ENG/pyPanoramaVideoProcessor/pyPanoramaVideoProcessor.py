import sys
import cv2
import numpy as np
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox,
    QProgressBar, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

# v.1.0.0 rev 5 by MoonDragon (Automatic system added to determine video progress)
# https://github.com/MoonDragon-MD/pyPanoramaVideoProcessor

class DragDropWidget(QFrame):
    def __init__(self, parent, line_edit):
        super().__init__(parent)
        self.line_edit = line_edit
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Box)
        self.setFixedHeight(100)
        self.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #888;")

        layout = QVBoxLayout(self)
        self.label = QLabel("Drag the video here or click 'Browse...'", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi')):
                self.line_edit.setText(file_path)
                self.label.setText(f"Video: {os.path.basename(file_path)}")
                break

class PanoramaApp(QMainWindow):
    VERSION = "1.0.0 rev 5 by MoonDragon"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panorama Video Processor")
        self.setGeometry(100, 100, 600, 600)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Section 1: Panorama Generation
        layout.addWidget(QLabel("<b>Step 1: Generate Panorama</b>"))
        step1_layout = QVBoxLayout()

        # Input video with drag and drop
        self.input_video = QLineEdit("input_verticale.mp4")
        self.input_video.setReadOnly(True)
        step1_layout.addWidget(QLabel("Imput video:"))
        self.drag_drop_area = DragDropWidget(self, self.input_video)
        step1_layout.addWidget(self.drag_drop_area)
        btn_browse_video = QPushButton("Browse...")
        btn_browse_video.clicked.connect(self.browse_input_video)
        step1_layout.addWidget(btn_browse_video)

        # Parameters with information buttons
        param_layout = QHBoxLayout()
        self.frame_step = QSpinBox()
        self.frame_step.setRange(1, 10)
        self.frame_step.setValue(1)
        param_layout.addWidget(QLabel("Frame step:"))
        param_layout.addWidget(self.frame_step)
        btn_info_frame = QPushButton("i")
        btn_info_frame.setFixedSize(20, 20)
        btn_info_frame.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Frame step' defines the number of frames to skip during panorama generation. A value of 1 means that every frame of the video is used, ensuring maximum continuity but increasing processing time. Higher values ​​(e.g. 2 or 3) process one frame every two or three, reducing the number of frames processed, which speeds up processing but can reduce the smoothness of the panorama. The range is 1 to 10."))
        param_layout.addWidget(btn_info_frame)
        step1_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.blend_width = QSpinBox()
        self.blend_width.setRange(10, 200)
        self.blend_width.setValue(100)
        param_layout.addWidget(QLabel("Blend width:"))
        param_layout.addWidget(self.blend_width)
        btn_info_blend = QPushButton("i")
        btn_info_blend.setFixedSize(20, 20)
        btn_info_blend.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Blend width' specifies the width in pixels of the blend zone between consecutive frames when creating the panorama. This overlap zone is used to combine frames smoothly, avoiding visual discontinuities. A higher value (e.g. 150-200) produces smoother transitions but increases the computational load, while a lower value (e.g. 10-50) is faster but may result in less smooth splices. The range is between 10 and 200 pixels."))
        param_layout.addWidget(btn_info_blend)
        step1_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.canvas_width = QSpinBox()
        self.canvas_width.setRange(10000, 100000)
        self.canvas_width.setSingleStep(1000)
        self.canvas_width.setValue(50000)
        param_layout.addWidget(QLabel("Canvas width:"))
        param_layout.addWidget(self.canvas_width)
        btn_info_canvas = QPushButton("i")
        btn_info_canvas.setFixedSize(20, 20)
        btn_info_canvas.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Canvas width' defines the width in pixels of the virtual canvas on which the video frames are aligned and joined to create the panorama. A value that is too small (e.g. close to 10,000) may truncate the panorama if the video covers a large scene, while a value that is too large (e.g. close to 100,000) increases memory use without significant benefit. The default value is 50,000 pixels, which is suitable for most videos. The configurable range is between 10,000 and 100,000 pixels, in 1,000 pixel increments."))
        param_layout.addWidget(btn_info_canvas)
        step1_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.direction = QComboBox()
        self.direction.addItems(["right", "left", "Automatic (slow)"])
        param_layout.addWidget(QLabel("Direction:"))
        param_layout.addWidget(self.direction)
        btn_info_dir = QPushButton("i")
        btn_info_dir.setFixedSize(20, 20)
        btn_info_dir.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Direction' determines the direction in which the panorama scrolls during generation. Choosing 'Right' aligns the frames to the right, useful when the camera goes from left to right in the video. Choosing 'Left' aligns the frames to the left, suitable when the camera moves from right to left. 'Automatic (slow)' automatically detects direction using affine transformations, calculating translations, rotations, and deriving velocity and acceleration for perfect synchronization, but is slower. The choice must reflect the movement of the camera to obtain a coherent panorama."))
        param_layout.addWidget(btn_info_dir)
        step1_layout.addLayout(param_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        step1_layout.addWidget(self.progress_bar)

        # Button to perform the first step
        btn_generate = QPushButton("Generate Panorama")
        btn_generate.clicked.connect(self.generate_panorama)
        step1_layout.addWidget(btn_generate)

        layout.addLayout(step1_layout)

        # Section 2: Video Generation
        layout.addWidget(QLabel("<b>Step 2: Generate Final Video</b>"))
        step2_layout = QVBoxLayout()

        # Panorama e shifts
        self.panorama_image = QLineEdit("panorama_generato.png")
        self.panorama_image.setReadOnly(True)
        step2_layout.addWidget(QLabel("Panorama PNG:"))
        step2_layout.addWidget(self.panorama_image)
        btn_browse_png = QPushButton("Browse...")
        btn_browse_png.clicked.connect(self.browse_panorama)
        step2_layout.addWidget(btn_browse_png)

        self.shifts_file = QLineEdit("shifts.json")
        self.shifts_file.setReadOnly(True)
        step2_layout.addWidget(QLabel("File shifts.json:"))
        step2_layout.addWidget(self.shifts_file)
        btn_browse_shifts = QPushButton("Browse...")
        btn_browse_shifts.clicked.connect(self.browse_shifts)
        step2_layout.addWidget(btn_browse_shifts)

        # Added drop-down menu for direction
        param_layout = QHBoxLayout()
        self.direction_step2 = QComboBox()
        self.direction_step2.addItems(["right", "left", "auto"])
        param_layout.addWidget(QLabel("Direction:"))
        param_layout.addWidget(self.direction_step2)
        btn_info_dir2 = QPushButton("i")
        btn_info_dir2.setFixedSize(20, 20)
        btn_info_dir2.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Direction' determines the direction in which the panorama scrolls in the final video. 'Right' scrolls the panorama to the right, 'Left' to the left. The 'Auto' option automatically infers the direction from the shifts.json file, based on the progress of cumulative shifts. If inference is not possible, the direction set in Step 1 is used. This option is useful for maintaining consistency with camera movement without manual intervention."))
        param_layout.addWidget(btn_info_dir2)
        step2_layout.addLayout(param_layout)

        # Synchronization parameters with information buttons
        param_layout = QHBoxLayout()
        self.shift_scale_mode = QComboBox()
        self.shift_scale_mode.addItems(["Normal", "Decelerate (0.98)", "Acceleration (1.11)", "Customized"])
        param_layout.addWidget(QLabel("Scale shift mode:"))
        param_layout.addWidget(self.shift_scale_mode)
        btn_info_shift = QPushButton("i")
        btn_info_shift.setFixedSize(20, 20)
        btn_info_shift.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "'Scale shift mode' controls the speed at which the panorama scrolls in the final video compared to the shifts calculated in Step 1. 'Normal' uses the automatically calculated speed, proportional to the length of the panorama. 'Deceleratete (0.98)' slows movement slightly (reducing speed by 2%), 'Accelerationte (1.11)' increases it by 11%. 'Custom' allows you to specify a manual value (between 0.5 and 2.0) to fine-tune the speed, useful for particular synchronizations or specific visual effects."))
        param_layout.addWidget(btn_info_shift)
        step2_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.shift_scale_value = QDoubleSpinBox()
        self.shift_scale_value.setRange(0.5, 2.0)
        self.shift_scale_value.setSingleStep(0.01)
        self.shift_scale_value.setValue(1.11)
        self.shift_scale_value.setEnabled(False)
        param_layout.addWidget(QLabel("Custom shift scale value:"))
        param_layout.addWidget(self.shift_scale_value)
        btn_info_shift_val = QPushButton("i")
        btn_info_shift_val.setFixedSize(20, 20)
        btn_info_shift_val.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Custom scale shift value' is only active when the scale shift mode is set to 'Custom'. Allows you to specify a scale factor (between 0.5 and 2.0) to adjust the scrolling speed of the panorama with respect to the calculated shifts. Values lower than 1 slow down the movement, values higher than 1 speed it up. For example, a value of 1.5 increases speed by 50%, while 0.8 reduces speed by 20%."))
        param_layout.addWidget(btn_info_shift_val)
        step2_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.offset_mode = QComboBox()
        self.offset_mode.addItems(["Normal", "Fixed Offset (-50 px)", "Progressive Offset (+0.087 px/frame)", "Customized"])
        param_layout.addWidget(QLabel("Offset mode:"))
        param_layout.addWidget(self.offset_mode)
        btn_info_offset = QPushButton("i")
        btn_info_offset.setFixedSize(20, 20)
        btn_info_offset.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "'Offset Mode' adjusts the starting position of the panorama in the final video compared to the original video. 'Normal' uses the calculated shifts without modification. 'Fixed offset (-50 px)' applies a constant offset of -50 pixels for each frame. 'Progressive offset (+0.087 px/frame)' adds an increasing shift of 0.087 pixels for each frame, useful for compensating small misalignments. 'Custom' allows you to specify a manual value for a custom progressive shift, giving you maximum control over alignment."))
        param_layout.addWidget(btn_info_offset)
        step2_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.offset_value = QDoubleSpinBox()
        self.offset_value.setRange(-100, 100)
        self.offset_value.setSingleStep(0.01)
        self.offset_value.setValue(0.087)
        self.offset_value.setEnabled(False)
        param_layout.addWidget(QLabel("Valore offset personalizzato:"))
        param_layout.addWidget(self.offset_value)
        btn_info_offset_val = QPushButton("i")
        btn_info_offset_val.setFixedSize(20, 20)
        btn_info_offset_val.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Custom Offset Value' is only active when the offset mode is set to 'Custom'. Specifies a progressive shift in pixels per frame (between -100 and 100) to add to the calculated shifts. Positive values move the panorama forward in time, negative values backwards. For example, a value of 0.087 adds 0.087 pixels of shift per frame, while -0.5 subtracts 0.5 pixels per frame, useful for micro-adjustments of sync."))
        param_layout.addWidget(btn_info_offset_val)
        step2_layout.addLayout(param_layout)

        # Nuovo parametro: Black padding at end
        param_layout = QHBoxLayout()
        self.black_padding = QSpinBox()
        self.black_padding.setRange(0, 10000)
        self.black_padding.setValue(0)
        param_layout.addWidget(QLabel("Black padding at end:"))
        param_layout.addWidget(self.black_padding)
        btn_info_black = QPushButton("i")
        btn_info_black.setFixedSize(20, 20)
        btn_info_black.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "The 'Black padding at end' defines the width in pixels of a black space to be added to the end (or beginning, depending on the direction) of the panorama strip. A value of 0 means that no padding is added, leaving the panorama unchanged. Higher values (e.g. 500 or 1000 pixels) add black space to compensate for length or synchronization discrepancies between the panorama and the video, improving visual alignment. The range is between 0 and 10,000 pixels."))
        param_layout.addWidget(btn_info_black)
        step2_layout.addLayout(param_layout)

        # Progress bar for the second step
        self.progress_bar_video = QProgressBar()
        self.progress_bar_video.setVisible(False)
        step2_layout.addWidget(self.progress_bar_video)

        # Button to perform the second step
        btn_convert = QPushButton("Generate Video MP4")
        btn_convert.clicked.connect(self.generate_video)
        step2_layout.addWidget(btn_convert)

        layout.addLayout(step2_layout)

        # Program version
        layout.addWidget(QLabel(f"Version: {self.VERSION}", alignment=Qt.AlignRight))

        layout.addStretch()

        # Enable/disable custom fields
        self.shift_scale_mode.currentIndexChanged.connect(self.toggle_shift_scale)
        self.offset_mode.currentIndexChanged.connect(self.toggle_offset)

    def browse_input_video(self):
        file, _ = QFileDialog.getOpenFileName(self, "Seleziona video", "", "Video Files (*.mp4 *.avi)")
        if file:
            self.input_video.setText(file)
            self.drag_drop_area.label.setText(f"Video: {os.path.basename(file)}")

    def browse_panorama(self):
        file, _ = QFileDialog.getOpenFileName(self, "Seleziona panorama", "", "Image Files (*.png)")
        if file:
            self.panorama_image.setText(file)

    def browse_shifts(self):
        file, _ = QFileDialog.getOpenFileName(self, "Seleziona shifts.json", "", "JSON Files (*.json)")
        if file:
            self.shifts_file.setText(file)

    def toggle_shift_scale(self):
        self.shift_scale_value.setEnabled(self.shift_scale_mode.currentText() == "Customized")

    def toggle_offset(self):
        self.offset_value.setEnabled(self.offset_mode.currentText() == "Customized")

    def generate_panorama(self):
        input_video = self.input_video.text()
        frame_step = self.frame_step.value()
        blend_width = self.blend_width.value()
        canvas_width = self.canvas_width.value()
        direction = self.direction.currentText()

        if not os.path.exists(input_video):
            QMessageBox.critical(self, "Errore", "Il file video di input non esiste!")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        try:
            run_generate_panorama(input_video, frame_step, blend_width, canvas_width, direction, self.progress_bar)
            QMessageBox.information(self, "Success", "Panorama and shifts.json generated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante la generazione del panorama: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def generate_video(self):
        panorama_image = self.panorama_image.text()
        shifts_file = self.shifts_file.text()
        input_video = self.input_video.text()
        shift_scale_mode = self.shift_scale_mode.currentText()
        offset_mode = self.offset_mode.currentText()
        shift_scale_value = self.shift_scale_value.value()
        offset_value = self.offset_value.value()
        direction = self.direction_step2.currentText()
        black_padding = self.black_padding.value()

        # File existence check
        if not os.path.exists(panorama_image):
            QMessageBox.critical(self, "Errore", "Il file panorama_generato.png non esiste!")
            return
        if not os.path.exists(shifts_file):
            QMessageBox.critical(self, "Errore", "Il file shifts.json non esiste!")
            return
        if not os.path.exists(input_video):
            QMessageBox.critical(self, "Errore", "Il file video di input non esiste!")
            return

        # Management of "auto" mode for direction
        if direction == "auto":
            try:
                with open(shifts_file, 'r') as f:
                    shifts = json.load(f)
                if len(shifts) > 1:
                    # If the cumulative shifts increase, direction is "right", otherwise "left"
                    direction = "right" if shifts[-1] > shifts[0] else "left"
                else:
                    # Fallback on the direction of step 1
                    direction = self.direction.currentText()
            except Exception as e:
                QMessageBox.warning(self, "Attenzione", f"Impossibile dedurre la direzione da shifts.json: {str(e)}. Uso la direzione dello step 1.")
                direction = self.direction.currentText()

        self.progress_bar_video.setVisible(True)
        self.progress_bar_video.setValue(0)
        QApplication.processEvents()

        try:
            run_generate_video(input_video, panorama_image, shifts_file, shift_scale_mode, offset_mode, shift_scale_value, offset_value, direction, self.progress_bar_video, black_padding)
            QMessageBox.information(self, "Success", "MP4 video generated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating video: {str(e)}")
        finally:
            self.progress_bar_video.setVisible(False)

def run_generate_panorama(input_video, frame_step, blend_width, canvas_width, direction, progress_bar):
    output_image = "panorama_generato.png"
    output_shifts = "shifts.json"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = f"temp_slit_{timestamp}"
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Temporary folder created: {temp_dir}")

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise Exception("Unable to open video.")

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video uploaded: {total_frames} frame, resolution: {frame_width}x{frame_height}")

    orb = cv2.ORB_create(5000)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    canvas_height = frame_height
    panorama = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    center_x = canvas_width // 2

    if direction == "Automatic (slow)":
        # Pre-step to determine direction using affine transformations
        print("Pre-pass for automatic direction determination...")
        cap_pre = cv2.VideoCapture(input_video)
        last_gray_pre = None
        dx_sum = 0
        count = 0
        frame_idx_pre = 0
        pre_step = max(1, frame_step * 2)  # Use a larger step for the pre-step to accelerate
        while True:
            cap_pre.set(cv2.CAP_PROP_POS_FRAMES, frame_idx_pre)
            ret, frame_pre = cap_pre.read()
            if not ret:
                break
            gray_pre = cv2.cvtColor(frame_pre, cv2.COLOR_BGR2GRAY)
            if last_gray_pre is not None:
                kp1, des1 = orb.detectAndCompute(last_gray_pre, None)
                kp2, des2 = orb.detectAndCompute(gray_pre, None)
                if des1 is not None and des2 is not None and len(kp1) > 5 and len(kp2) > 5:
                    matches = sorted(bf.match(des1, des2), key=lambda x: x.distance)[:50]
                    if len(matches) >= 4:
                        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches])
                        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches])
                        M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=5.0)
                        if M is not None:
                            raw_dx = M[0, 2]  # tx
                            dx_sum += raw_dx
                            count += 1
            last_gray_pre = gray_pre
            frame_idx_pre += pre_step
        cap_pre.release()
        if count > 0:
            avg_dx = dx_sum / count
            if avg_dx < 0:
                direction = "right"
            else:
                direction = "left"
        else:
            raise Exception("Unable to determine automatic direction.")
        print(f"Direction determined automatically: {direction}")

    direction_sign = 1 if direction == "right" else -1

    if direction != "Automatic (slow)":
        # Modo veloce originale
        current_x = center_x
        last_gray = None
        last_frame = None
        strip_count = 0
        frame_idx = 0
        cumulative_shifts = []
        max_strips = total_frames // frame_step
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret or strip_count >= max_strips:
                break

            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            dx = 10

            if last_gray is not None:
                kp1, des1 = orb.detectAndCompute(last_gray, None)
                kp2, des2 = orb.detectAndCompute(frame_gray, None)

                if des1 is not None and des2 is not None and len(kp1) > 5 and len(kp2) > 5:
                    matches = sorted(bf.match(des1, des2), key=lambda x: x.distance)[:50]
                    if len(matches) >= 10:
                        dxs = [kp2[m.trainIdx].pt[0] - kp1[m.queryIdx].pt[0] for m in matches]
                        dxs = np.array(dxs)
                        q1, q3 = np.percentile(dxs, [25, 75])
                        iqr = q3 - q1
                        valid_dxs = dxs[(dxs >= q1 - 1.5 * iqr) & (dxs <= q3 + 1.5 * iqr)]
                        if len(valid_dxs) > 0:
                            dx = np.median(valid_dxs)
                        print(f"Frame {frame_idx}: {len(matches)} matches, dx={dx}, valid_dxs={len(valid_dxs)}")
                    else:
                        print(f"Frame {frame_idx}: insufficienti match ({len(matches)}), usato dx={dx}")

            dx = max(dx, 10)
            current_x += direction_sign * dx
            cumulative_shifts.append(abs(current_x - center_x))

            if current_x < 0 or current_x + frame_width > canvas_width:
                print("Reached the edges of the canvas.")
                break

            overlap = min(blend_width, frame_width)
            current_y = 0

            if last_frame is not None:
                blend_a = panorama[current_y:current_y + frame_height, current_x:current_x + overlap]
                blend_b = frame[:, :overlap]
                if blend_a.shape == blend_b.shape:
                    alpha = np.linspace(0, 1, overlap)[None, :, None]
                    blended = (1 - alpha) * blend_a + alpha * blend_b
                    blended = blended.astype(np.uint8)
                    panorama[current_y:current_y + frame_height, current_x:current_x + overlap] = blended
            panorama[current_y:current_y + frame_height, current_x + overlap:current_x + frame_width] = frame[:, overlap:]

            cv2.imwrite(os.path.join(temp_dir, f"frame_{strip_count:04d}.png"), frame)

            last_gray = frame_gray.copy()
            last_frame = frame.copy()
            strip_count += 1
            frame_idx += frame_step

            # Aggiorna barra di avanzamento
            progress = int((strip_count / max_strips) * 100)
            progress_bar.setValue(progress)
            QApplication.processEvents()
    else:
        # Automatic slow mode for perfect synchronization
        print("Slow auto mode: Process all frames for perfect sync...")
        current_x = center_x
        last_gray = None
        last_frame = None
        strip_count = 0
        frame_idx = 0
        cumulative_shifts = []
        velocities = []  # For speed (dx per frame)
        accelerations = []  # For acceleration (right delta)
        last_dx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            dx = 10
            raw_dx = 0

            if last_gray is not None:
                kp1, des1 = orb.detectAndCompute(last_gray, None)
                kp2, des2 = orb.detectAndCompute(frame_gray, None)

                if des1 is not None and des2 is not None and len(kp1) > 5 and len(kp2) > 5:
                    matches = sorted(bf.match(des1, des2), key=lambda x: x.distance)[:50]
                    if len(matches) >= 4:
                        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches])
                        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches])
                        M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=5.0)
                        if M is not None:
                            raw_dx = M[0, 2]  # tx come raw_dx
                            ty = M[1, 2]  # y translation (ignored for now)
                            theta = np.degrees(np.arctan2(M[1, 0], M[0, 0]))  # rotazione (ignorata per ora)
                            print(f"Frame {frame_idx}: tx={raw_dx}, ty={ty}, theta={theta}")
                            dx = -direction_sign * raw_dx  # Make dx positive based on direction
                            dx = max(dx, 10)
                            velocity = dx  # Siccome dt=1 frame
                            velocities.append(velocity)
                            acceleration = velocity - last_dx
                            accelerations.append(acceleration)
                            last_dx = velocity

            current_x += direction_sign * dx
            cumulative_shifts.append(abs(current_x - center_x))

            if current_x < 0 or current_x + frame_width > canvas_width:
                print("Reached the edges of the canvas.")
                break

            if frame_idx % frame_step == 0:
                overlap = min(blend_width, frame_width)
                current_y = 0

                if last_frame is not None:
                    if direction_sign == 1:
                        blend_a = panorama[current_y:current_y + frame_height, current_x:current_x + overlap]
                        blend_b = frame[:, :overlap]
                        if blend_a.shape == blend_b.shape:
                            alpha = np.linspace(0, 1, overlap)[None, :, None]
                            blended = (1 - alpha) * blend_a + alpha * blend_b
                            blended = blended.astype(np.uint8)
                            panorama[current_y:current_y + frame_height, current_x:current_x + overlap] = blended
                        panorama[current_y:current_y + frame_height, current_x + overlap:current_x + frame_width] = frame[:, overlap:]
                    else:
                        blend_a = panorama[current_y:current_y + frame_height, current_x + frame_width - overlap:current_x + frame_width]
                        blend_b = frame[:, -overlap:]
                        if blend_a.shape == blend_b.shape:
                            alpha = np.linspace(0, 1, overlap)[None, :, None]
                            blended = (1 - alpha) * blend_b + alpha * blend_a
                            blended = blended.astype(np.uint8)
                            panorama[current_y:current_y + frame_height, current_x + frame_width - overlap:current_x + frame_width] = blended
                        panorama[current_y:current_y + frame_height, current_x:current_x + frame_width - overlap] = frame[:, :-overlap]
                else:
                    panorama[current_y:current_y + frame_height, current_x:current_x + frame_width] = frame

                cv2.imwrite(os.path.join(temp_dir, f"frame_{strip_count:04d}.png"), frame)
                last_frame = frame.copy()
                strip_count += 1

            last_gray = frame_gray.copy()
            frame_idx += 1

            # Aggiorna barra di avanzamento
            progress = int((frame_idx / total_frames) * 100)
            progress_bar.setValue(progress)
            QApplication.processEvents()

        # Velocities and accelerations are calculated but not used for now

    cap.release()
    gray = cv2.cvtColor(panorama, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    x, y, w, h = cv2.boundingRect(thresh)
    final_panorama = panorama[y:y + h, x:x + w]
    cv2.imwrite(output_image, final_panorama)

    with open(output_shifts, 'w') as f:
        json.dump(cumulative_shifts, f)
    print(f"Panorama salvato: {output_image}")
    print(f"Shift cumulativi salvati: {output_shifts}")
    print(f"Frame temporanei salvati in: {temp_dir}")

def run_generate_video(input_video, panorama_image, shifts_file, shift_scale_mode, offset_mode, shift_scale_value, offset_value, direction, progress_bar, black_padding=0):
    output_video = "output_finale.mp4"

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise Exception("Unable to open video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    panorama = cv2.imread(panorama_image)
    if panorama is None:
        raise Exception("Error loading panorama!")

    panorama = cv2.resize(panorama, (panorama.shape[1], frame_height))

    # Add a black piece to the end of the png stripe only if black_padding > 0
    if black_padding > 0:
        if black_padding > 100000:  # Arbitrary limit to avoid excessive padding
            raise Exception("The black padding value is too large!")
        black = np.zeros((frame_height, black_padding, 3), dtype=np.uint8)
        if direction == "right":
            panorama = np.hstack((black, panorama))
        else:
            panorama = np.hstack((panorama, black))
        print(f"Added black padding {black_padding} pixel")
    else:
        print("No black padding added (black_padding = 0)")

    pan_width = panorama.shape[1]

    with open(shifts_file, 'r') as f:
        cumulative_shifts = json.load(f)

    output_width = frame_width * 3
    static_width = frame_width
    scroll_width = frame_width * 2

    if pan_width < scroll_width + static_width:
        raise Exception(f"Il panorama è troppo corto ({pan_width}px), serve almeno {scroll_width + static_width}px!")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video, fourcc, fps, (output_width, frame_height))

    initial_shift = cumulative_shifts[0] if cumulative_shifts else frame_width
    max_shift = cumulative_shifts[-1] - initial_shift if cumulative_shifts else pan_width - scroll_width

    # Imposta shift_scale
    if shift_scale_mode == "Normal":
        shift_scale = (pan_width - scroll_width) / max_shift if max_shift > 0 else 1
    elif shift_scale_mode == "Decelerate (0.98)":
        shift_scale = (pan_width - scroll_width) / max_shift * 0.98
    elif shift_scale_mode == "Acceleration (1.11)":
        shift_scale = (pan_width - scroll_width) / max_shift * 1.11
    else:
        shift_scale = (pan_width - scroll_width) / max_shift * shift_scale_value

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        pano_slice = np.zeros((frame_height, scroll_width, 3), dtype=np.uint8)

        if frame_idx < len(cumulative_shifts):
            offset = int((cumulative_shifts[frame_idx] - initial_shift) * shift_scale)
            if offset_mode == "Fixed Offset (-50 px)":
                offset -= 50
            elif offset_mode == "Progressive Offset (+0.087 px/frame)":
                offset += int(frame_idx * 0.087)
            elif offset_mode == "Customized":
                offset += int(frame_idx * offset_value)
        else:
            offset = int(frame_idx * (pan_width - scroll_width) / max(frame_count - 1, 1))

        if direction == "right":
            if offset <= 0:
                pano_slice[:, :] = 0
            elif offset <= scroll_width:
                pano_part = panorama[:, initial_shift:initial_shift + offset]
                if pano_part.shape[1] > 0:
                    pano_slice[:, scroll_width - offset:scroll_width] = pano_part
            else:
                start_x = initial_shift + offset - scroll_width
                if start_x + scroll_width <= pan_width:
                    pano_slice[:, :] = panorama[:, start_x:start_x + scroll_width]
                else:
                    pano_slice[:, :pan_width - start_x] = panorama[:, start_x:pan_width]
            combined = np.hstack((pano_slice, frame))
        else:  # left
            if offset <= 0:
                pano_slice[:, :] = 0
            elif offset <= scroll_width:
                pano_part = panorama[:, pan_width - offset:pan_width]
                if pano_part.shape[1] > 0:
                    pano_slice[:, :offset] = pano_part
            else:
                start_x = pan_width - offset
                if start_x >= 0:
                    pano_slice[:, :] = panorama[:, start_x:start_x + scroll_width]
                else:
                    pano_slice[:, -start_x:] = panorama[:, :start_x + scroll_width]
            combined = np.hstack((frame, pano_slice))

        out.write(combined)
        frame_idx += 1

        # Update progress bar
        progress = int((frame_idx / frame_count) * 100)
        progress_bar.setValue(progress)
        QApplication.processEvents()

    min_frames = int(fps * 5)
    while frame_idx < min_frames:
        out.write(combined)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"Final video created: {output_video}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PanoramaApp()
    window.show()
    sys.exit(app.exec_())

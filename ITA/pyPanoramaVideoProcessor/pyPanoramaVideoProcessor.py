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

# v.1.0.0 rev 5 by MoonDragon (aggiunta sistema Automatico per determinare andamento video)
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
        self.label = QLabel("Trascina qui il video o clicca 'Sfoglia...'", self)
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

        # Sezione 1: Generazione Panorama
        layout.addWidget(QLabel("<b>Step 1: Genera Panorama</b>"))
        step1_layout = QVBoxLayout()

        # Input video con drag and drop
        self.input_video = QLineEdit("input_verticale.mp4")
        self.input_video.setReadOnly(True)
        step1_layout.addWidget(QLabel("Video di input:"))
        self.drag_drop_area = DragDropWidget(self, self.input_video)
        step1_layout.addWidget(self.drag_drop_area)
        btn_browse_video = QPushButton("Sfoglia...")
        btn_browse_video.clicked.connect(self.browse_input_video)
        step1_layout.addWidget(btn_browse_video)

        # Parametri con pulsanti informativi
        param_layout = QHBoxLayout()
        self.frame_step = QSpinBox()
        self.frame_step.setRange(1, 10)
        self.frame_step.setValue(1)
        param_layout.addWidget(QLabel("Frame step:"))
        param_layout.addWidget(self.frame_step)
        btn_info_frame = QPushButton("i")
        btn_info_frame.setFixedSize(20, 20)
        btn_info_frame.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "Il 'Frame step' definisce il numero di frame da saltare durante la generazione del panorama. Un valore di 1 significa che ogni frame del video viene utilizzato, garantendo la massima continuità ma aumentando il tempo di elaborazione. Valori più alti (es. 2 o 3) elaborano un frame ogni due o tre, riducendo il numero di frame processati, il che accelera l'elaborazione ma può ridurre la fluidità del panorama. L'intervallo è compreso tra 1 e 10."))
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
            "Il 'Blend width' specifica la larghezza in pixel della zona di fusione tra frame consecutivi durante la creazione del panorama. Questa zona di sovrapposizione viene utilizzata per combinare i frame in modo fluido, evitando discontinuità visive. Un valore più alto (es. 150-200) produce transizioni più morbide ma aumenta il carico computazionale, mentre un valore più basso (es. 10-50) è più veloce ma potrebbe risultare in giunzioni meno uniformi. L'intervallo è compreso tra 10 e 200 pixel."))
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
            "Il 'Canvas width' definisce la larghezza in pixel del canvas virtuale su cui i frame del video vengono allineati e uniti per creare il panorama. Un valore troppo piccolo (es. vicino a 10.000) potrebbe troncare il panorama se il video copre un'ampia scena, mentre un valore troppo grande (es. vicino a 100.000) aumenta l'uso di memoria senza benefici significativi. Il valore predefinito è 50.000 pixel, adatto per la maggior parte dei video. L'intervallo configurabile è tra 10.000 e 100.000 pixel, con incrementi di 1.000 pixel."))
        param_layout.addWidget(btn_info_canvas)
        step1_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.direction = QComboBox()
        self.direction.addItems(["destra", "sinistra", "Automatico (lento)"])
        param_layout.addWidget(QLabel("Direzione:"))
        param_layout.addWidget(self.direction)
        btn_info_dir = QPushButton("i")
        btn_info_dir.setFixedSize(20, 20)
        btn_info_dir.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "La 'Direzione' determina il verso di scorrimento del panorama durante la generazione. Scegliere 'Destra' allinea i frame verso destra, utile quando la telecamera va da sinistra a destra nel video. Scegliere 'Sinistra' allinea i frame verso sinistra, adatto quando la telecamera si muove da destra a sinistra. 'Automatico (lento)' rileva automaticamente la direzione usando trasformazioni affini, calcolando traslazioni, rotazioni e derivando velocità e accelerazione per una sincronia perfetta, ma è più lento. La scelta deve riflettere il movimento della telecamera per ottenere un panorama coerente."))
        param_layout.addWidget(btn_info_dir)
        step1_layout.addLayout(param_layout)

        # Barra di avanzamento
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        step1_layout.addWidget(self.progress_bar)

        # Pulsante per eseguire il primo step
        btn_generate = QPushButton("Genera Panorama")
        btn_generate.clicked.connect(self.generate_panorama)
        step1_layout.addWidget(btn_generate)

        layout.addLayout(step1_layout)

        # Sezione 2: Generazione Video
        layout.addWidget(QLabel("<b>Step 2: Genera Video Finale</b>"))
        step2_layout = QVBoxLayout()

        # Panorama e shifts
        self.panorama_image = QLineEdit("panorama_generato.png")
        self.panorama_image.setReadOnly(True)
        step2_layout.addWidget(QLabel("Panorama PNG:"))
        step2_layout.addWidget(self.panorama_image)
        btn_browse_png = QPushButton("Sfoglia...")
        btn_browse_png.clicked.connect(self.browse_panorama)
        step2_layout.addWidget(btn_browse_png)

        self.shifts_file = QLineEdit("shifts.json")
        self.shifts_file.setReadOnly(True)
        step2_layout.addWidget(QLabel("File shifts.json:"))
        step2_layout.addWidget(self.shifts_file)
        btn_browse_shifts = QPushButton("Sfoglia...")
        btn_browse_shifts.clicked.connect(self.browse_shifts)
        step2_layout.addWidget(btn_browse_shifts)

        # Aggiunta del menu a tendina per la direzione
        param_layout = QHBoxLayout()
        self.direction_step2 = QComboBox()
        self.direction_step2.addItems(["destra", "sinistra", "auto"])
        param_layout.addWidget(QLabel("Direzione:"))
        param_layout.addWidget(self.direction_step2)
        btn_info_dir2 = QPushButton("i")
        btn_info_dir2.setFixedSize(20, 20)
        btn_info_dir2.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "La 'Direzione' determina il verso di scorrimento del panorama nel video finale. 'Destra' fa scorrere il panorama verso destra, 'Sinistra' verso sinistra. L'opzione 'Auto' deduce automaticamente la direzione dal file shifts.json, basandosi sull'andamento degli shift cumulativi. Se la deduzione non è possibile, viene usata la direzione impostata nello Step 1. Questa opzione è utile per mantenere la coerenza con il movimento della telecamera senza intervento manuale."))
        param_layout.addWidget(btn_info_dir2)
        step2_layout.addLayout(param_layout)

        # Parametri di sincronizzazione con pulsanti informativi
        param_layout = QHBoxLayout()
        self.shift_scale_mode = QComboBox()
        self.shift_scale_mode.addItems(["Normale", "Decelera (0.98)", "Accelera (1.11)", "Personalizzato"])
        param_layout.addWidget(QLabel("Modalità shift scale:"))
        param_layout.addWidget(self.shift_scale_mode)
        btn_info_shift = QPushButton("i")
        btn_info_shift.setFixedSize(20, 20)
        btn_info_shift.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "La 'Modalità shift scale' controlla la velocità di scorrimento del panorama nel video finale rispetto agli shift calcolati nello Step 1. 'Normale' usa la velocità calcolata automaticamente, proporzionale alla lunghezza del panorama. 'Decelera (0.98)' rallenta leggermente il movimento (riducendo la velocità del 2%), 'Accelera (1.11)' lo aumenta del 11%. 'Personalizzato' consente di specificare un valore manuale (tra 0.5 e 2.0) per regolare la velocità in modo fine, utile per sincronizzazioni particolari o effetti visivi specifici."))
        param_layout.addWidget(btn_info_shift)
        step2_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.shift_scale_value = QDoubleSpinBox()
        self.shift_scale_value.setRange(0.5, 2.0)
        self.shift_scale_value.setSingleStep(0.01)
        self.shift_scale_value.setValue(1.11)
        self.shift_scale_value.setEnabled(False)
        param_layout.addWidget(QLabel("Valore shift scale personalizzato:"))
        param_layout.addWidget(self.shift_scale_value)
        btn_info_shift_val = QPushButton("i")
        btn_info_shift_val.setFixedSize(20, 20)
        btn_info_shift_val.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "Il 'Valore shift scale personalizzato' è attivo solo quando la modalità shift scale è impostata su 'Personalizzato'. Permette di specificare un fattore di scala (tra 0.5 e 2.0) per regolare la velocità di scorrimento del panorama rispetto agli shift calcolati. Valori inferiori a 1 rallentano il movimento, valori superiori a 1 lo accelerano. Ad esempio, un valore di 1.5 aumenta la velocità del 50%, mentre 0.8 la riduce del 20%."))
        param_layout.addWidget(btn_info_shift_val)
        step2_layout.addLayout(param_layout)

        param_layout = QHBoxLayout()
        self.offset_mode = QComboBox()
        self.offset_mode.addItems(["Normale", "Offset fisso (-50 px)", "Offset progressivo (+0.087 px/frame)", "Personalizzato"])
        param_layout.addWidget(QLabel("Modalità offset:"))
        param_layout.addWidget(self.offset_mode)
        btn_info_offset = QPushButton("i")
        btn_info_offset.setFixedSize(20, 20)
        btn_info_offset.clicked.connect(lambda: QMessageBox.information(self, "Info", 
            "La 'Modalità offset' regola la posizione iniziale del panorama nel video finale rispetto al video originale. 'Normale' usa gli shift calcolati senza modifiche. 'Offset fisso (-50 px)' applica uno spostamento costante di -50 pixel per ogni frame. 'Offset progressivo (+0.087 px/frame)' aggiunge uno spostamento crescente di 0.087 pixel per ogni frame, utile per compensare piccoli disallineamenti. 'Personalizzato' permette di specificare un valore manuale per uno spostamento progressivo personalizzato, offrendo il massimo controllo sull'allineamento."))
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
            "Il 'Valore offset personalizzato' è attivo solo quando la modalità offset è impostata su 'Personalizzato'. Specifica uno spostamento progressivo in pixel per frame (tra -100 e 100) da aggiungere agli shift calcolati. Valori positivi spostano il panorama in avanti nel tempo, valori negativi all'indietro. Ad esempio, un valore di 0.087 aggiunge 0.087 pixel di spostamento per ogni frame, mentre -0.5 sottrae 0.5 pixel per frame, utile per micro-regolazioni di sincronizzazione."))
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
            "Il 'Black padding at end' definisce la larghezza in pixel di uno spazio nero da aggiungere alla fine (o all'inizio, a seconda della direzione) della striscia panorama. Un valore di 0 significa che non viene aggiunto alcun padding, lasciando il panorama invariato. Valori maggiori (es. 500 o 1000 pixel) aggiungono uno spazio nero per compensare discrepanze di lunghezza o sincronizzazione tra il panorama e il video, migliorando l'allineamento visivo. L'intervallo è tra 0 e 10.000 pixel."))
        param_layout.addWidget(btn_info_black)
        step2_layout.addLayout(param_layout)

        # Barra di avanzamento per il secondo step
        self.progress_bar_video = QProgressBar()
        self.progress_bar_video.setVisible(False)
        step2_layout.addWidget(self.progress_bar_video)

        # Pulsante per eseguire il secondo step
        btn_convert = QPushButton("Genera Video MP4")
        btn_convert.clicked.connect(self.generate_video)
        step2_layout.addWidget(btn_convert)

        layout.addLayout(step2_layout)

        # Versione del programma
        layout.addWidget(QLabel(f"Versione: {self.VERSION}", alignment=Qt.AlignRight))

        layout.addStretch()

        # Abilita/disabilita campi personalizzati
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
        self.shift_scale_value.setEnabled(self.shift_scale_mode.currentText() == "Personalizzato")

    def toggle_offset(self):
        self.offset_value.setEnabled(self.offset_mode.currentText() == "Personalizzato")

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
            QMessageBox.information(self, "Successo", "Panorama e shifts.json generati con successo!")
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

        # Controllo esistenza file
        if not os.path.exists(panorama_image):
            QMessageBox.critical(self, "Errore", "Il file panorama_generato.png non esiste!")
            return
        if not os.path.exists(shifts_file):
            QMessageBox.critical(self, "Errore", "Il file shifts.json non esiste!")
            return
        if not os.path.exists(input_video):
            QMessageBox.critical(self, "Errore", "Il file video di input non esiste!")
            return

        # Gestione modalità "auto" per la direzione
        if direction == "auto":
            try:
                with open(shifts_file, 'r') as f:
                    shifts = json.load(f)
                if len(shifts) > 1:
                    # Se gli shift cumulativi aumentano, direzione è "destra", altrimenti "sinistra"
                    direction = "destra" if shifts[-1] > shifts[0] else "sinistra"
                else:
                    # Fallback sulla direzione dello step 1
                    direction = self.direction.currentText()
            except Exception as e:
                QMessageBox.warning(self, "Attenzione", f"Impossibile dedurre la direzione da shifts.json: {str(e)}. Uso la direzione dello step 1.")
                direction = self.direction.currentText()

        self.progress_bar_video.setVisible(True)
        self.progress_bar_video.setValue(0)
        QApplication.processEvents()

        try:
            run_generate_video(input_video, panorama_image, shifts_file, shift_scale_mode, offset_mode, shift_scale_value, offset_value, direction, self.progress_bar_video, black_padding)
            QMessageBox.information(self, "Successo", "Video MP4 generato con successo!")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante la generazione del video: {str(e)}")
        finally:
            self.progress_bar_video.setVisible(False)

def run_generate_panorama(input_video, frame_step, blend_width, canvas_width, direction, progress_bar):
    output_image = "panorama_generato.png"
    output_shifts = "shifts.json"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = f"temp_slit_{timestamp}"
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Cartella temporanea creata: {temp_dir}")

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise Exception("Impossibile aprire il video.")

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video caricato: {total_frames} frame, risoluzione: {frame_width}x{frame_height}")

    orb = cv2.ORB_create(5000)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    canvas_height = frame_height
    panorama = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    center_x = canvas_width // 2

    if direction == "Automatico (lento)":
        # Pre-passaggio per determinare la direzione utilizzando trasformazioni affini
        print("Pre-pass per determinazione direzione automatica...")
        cap_pre = cv2.VideoCapture(input_video)
        last_gray_pre = None
        dx_sum = 0
        count = 0
        frame_idx_pre = 0
        pre_step = max(1, frame_step * 2)  # Utilizzare un passo più grande per il pre-passaggio per accelerare
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
                direction = "destra"
            else:
                direction = "sinistra"
        else:
            raise Exception("Impossibile determinare la direzione automatica.")
        print(f"Direzione determinata automaticamente: {direction}")

    direction_sign = 1 if direction == "destra" else -1

    if direction != "Automatico (lento)":
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
                print("Raggiunti i bordi del canvas.")
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
        # Modalità lenta automatica per una sincronizzazione perfetta
        print("Modalità automatica lenta: elaborazione di tutti i frame per sincronia perfetta...")
        current_x = center_x
        last_gray = None
        last_frame = None
        strip_count = 0
        frame_idx = 0
        cumulative_shifts = []
        velocities = []  # Per la velocità (dx per fotogramma)
        accelerations = []  # Per l'accelerazione (delta dx)
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
                            ty = M[1, 2]  # y traslazione (ignorata per ora)
                            theta = np.degrees(np.arctan2(M[1, 0], M[0, 0]))  # rotazione (ignorata per ora)
                            print(f"Frame {frame_idx}: tx={raw_dx}, ty={ty}, theta={theta}")
                            dx = -direction_sign * raw_dx  # Rendi dx positivo in base alla direzione
                            dx = max(dx, 10)
                            velocity = dx  # Siccome dt=1 frame
                            velocities.append(velocity)
                            acceleration = velocity - last_dx
                            accelerations.append(acceleration)
                            last_dx = velocity

            current_x += direction_sign * dx
            cumulative_shifts.append(abs(current_x - center_x))

            if current_x < 0 or current_x + frame_width > canvas_width:
                print("Raggiunti i bordi del canvas.")
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

        # Le velocità e le accelerazioni vengono calcolate ma non utilizzate per ora

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
        raise Exception("Impossibile aprire il video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    panorama = cv2.imread(panorama_image)
    if panorama is None:
        raise Exception("Errore nel caricamento del panorama!")

    panorama = cv2.resize(panorama, (panorama.shape[1], frame_height))

    # Aggiungi un pezzo nero alla fine della striscia png solo se black_padding > 0
    if black_padding > 0:
        if black_padding > 100000:  # Limite arbitrario per evitare padding eccessivi
            raise Exception("Il valore di black padding è troppo grande!")
        black = np.zeros((frame_height, black_padding, 3), dtype=np.uint8)
        if direction == "destra":
            panorama = np.hstack((black, panorama))
        else:
            panorama = np.hstack((panorama, black))
        print(f"Aggiunto padding nero di {black_padding} pixel")
    else:
        print("Nessun padding nero aggiunto (black_padding = 0)")

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
    if shift_scale_mode == "Normale":
        shift_scale = (pan_width - scroll_width) / max_shift if max_shift > 0 else 1
    elif shift_scale_mode == "Decelera (0.98)":
        shift_scale = (pan_width - scroll_width) / max_shift * 0.98
    elif shift_scale_mode == "Accelera (1.11)":
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
            if offset_mode == "Offset fisso (-50 px)":
                offset -= 50
            elif offset_mode == "Offset progressivo (+0.087 px/frame)":
                offset += int(frame_idx * 0.087)
            elif offset_mode == "Personalizzato":
                offset += int(frame_idx * offset_value)
        else:
            offset = int(frame_idx * (pan_width - scroll_width) / max(frame_count - 1, 1))

        if direction == "destra":
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
        else:  # sinistra
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

        # Aggiorna barra di avanzamento
        progress = int((frame_idx / frame_count) * 100)
        progress_bar.setValue(progress)
        QApplication.processEvents()

    min_frames = int(fps * 5)
    while frame_idx < min_frames:
        out.write(combined)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"Video finale creato: {output_video}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PanoramaApp()
    window.show()
    sys.exit(app.exec_())

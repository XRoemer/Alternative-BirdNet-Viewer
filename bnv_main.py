import numpy as np
from matplotlib import cm
from importlib import reload

# tflite has to be imported before pyqt, otherwise birdnet throws an error
# try:
#     import tflite_runtime.interpreter as tflite
# except ImportError:
#     from tensorflow.lite.python.interpreter import Interpreter as tflite

from tensorflow.lite.python.interpreter import Interpreter as tflite

import birdnet_analyzer
import bn_files
from bn_settings import Settings
from bn_audio import Audio
from bn_test import Lines_and_Text
    
from PyQt6.QtWidgets import QApplication, QWidget,QMainWindow, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtWidgets import QTabWidget, QTableWidget
from PyQt6.QtGui import QKeyEvent

import pyqtgraph as pg


class Main_Win(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spektrogramm-Viewer")
        self.setGeometry(600, 100, 1000, 600)        
        self.viewer = SpectrogramViewer()
        self.setCentralWidget(self.viewer)
        self.show()
        
    #     self.installEventFilter(self)
    #
    # def eventFilter(self, o, ev):
    #
    #     if ev.type() == 129: # It's a QHoverEvent, but QHoverEvent doesn't work
    #         if ev.modifiers().name == "ControlModifier":
    #             import bn_test 
    #             bn_test = reload(bn_test)
    #             bn_test.test3(self.viewer,o,ev)
    #     return super().eventFilter(o, ev)

class SVWindow(QWidget):
    def __init__(self,SV):
        super().__init__()
        
        self.SV = SV
        
    def keyPressEvent(self, event):
        if isinstance(event, QKeyEvent):
            key_text = event.key()
            if key_text == 16777248:
                self.SV.plot.setMouseEnabled(y=True)
                self.SV.plot.setMouseEnabled(x=False)
            if key_text == 16777249:
                self.SV.cmd_key = True
            if key_text == 32:
                self.SV.audio.toggle_playback()
                
    def keyReleaseEvent(self, event):
        if isinstance(event, QKeyEvent):
            key_text = event.key()
            if key_text == 16777248:
                self.SV.plot.setMouseEnabled(y=False)
                self.SV.plot.setMouseEnabled(x=True)
            if key_text == 16777249:
                self.SV.cmd_key = False
        
        
class FilesTable(QTableWidget):
    def __init__(self,SV):
        super().__init__()
        self.SV = SV
        self.cmd_key = False
        
    def keyPressEvent(self, event):
        if isinstance(event, QKeyEvent):
            key_text = event.key()
            if key_text == 16777249:
                self.cmd_key = True
        
    def keyReleaseEvent(self, event):
        if isinstance(event, QKeyEvent):
            key_text = event.key()
            if key_text == 16777249:
                self.cmd_key = False
        
        

class SpectrogramViewer(QWidget):
    def __init__(self):
        super().__init__()
        
        self.audio = Audio(self)
        self.files = bn_files.Files(self)
        self.lines = Lines_and_Text(self)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)
        
        self.create_files_tab()
        self.create_spectrogram_win()

        self.text_items = []

        self.loop_view = None 
        self.birdnet_analyzer = birdnet_analyzer
        self.shift_key = False
        self.cmd_key = False
        self.settings = Settings(self)
        
    def create_spectrogram_win(self):
        
        self.tab_plot = QWidget()
        self.tab_plot = SVWindow(self)
        tab1_layout = QVBoxLayout(self.tab_plot)
        self.init_spectro() # creates self.plot
        tab1_layout.addWidget(self.plot)
        self.tab1_layout = tab1_layout

        btn_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("test")
        self.test_btn.clicked.connect(self.test)
        btn_layout.addWidget(self.test_btn)
        
        reset_view = QPushButton("reset view")
        reset_view.clicked.connect(self.reset_view)
        btn_layout.addWidget(reset_view)
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.audio.toggle_playback)
        btn_layout.addWidget(self.play_btn)

        tab1_layout.addLayout(btn_layout)
        
        self.audio.timeline = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('r', width=2))
        self.plot.addItem(self.audio.timeline)
        
        self.tab_plot.show()
        

    def create_files_tab(self):
        
        main_widg = QWidget()
        main_layout = QVBoxLayout(main_widg)

        # === Tab 2: Marker-Tabelle ===
        self.tab_files_table = QWidget()
        tab2_layout = QHBoxLayout(self.tab_files_table)
        

        self.files_table = FilesTable(self) # QTableWidget(0, 23) 
        self.files_table.setColumnCount(23)
        entries = ["Load File", "Length", "Detect"]
        cfgs = ["detect-cfg" for i in range(20)]
        entries += cfgs
        self.files_table.setHorizontalHeaderLabels(entries)
        self.files.files_table = self.files_table
        self.files_table.clicked.connect(self.files.files_table_clicked)
        
        tab2_layout.addWidget(self.files_table)
        
        self.tab3 = QWidget()
        tab3_layout = QVBoxLayout(self.tab3)
        self.tab3.setFixedWidth(224) 
        tab2_layout.addWidget(self.tab3)
        
        main_layout.addWidget(self.tab_files_table)

        # Buttons im Tab 2
        btn_layout2 = QHBoxLayout()
        main_layout.addLayout(btn_layout2)

        self.fill_table_btn = QPushButton("load files")
        self.fill_table_btn.clicked.connect(self.files.load_files)
        btn_layout2.addWidget(self.fill_table_btn)

        self.start_BN = QPushButton("analyze_recording(s)")
        self.start_BN.clicked.connect(self.files.create_detections)
        btn_layout2.addWidget(self.start_BN)
        
        save = QPushButton("save current detection")
        save.clicked.connect(self.files.save_current_detection)
        btn_layout2.addWidget(save)
        
        save_all = QPushButton("save all detections")
        save_all.clicked.connect(self.files.save_all_detections)
        btn_layout2.addWidget(save_all)
        
        show_spectro = QPushButton("show spectrogramm")
        show_spectro.clicked.connect(self.show_spectro)
        btn_layout2.addWidget(show_spectro)
        
        self.test_btn = QPushButton("test")
        self.test_btn.clicked.connect(self.test)
        btn_layout2.addWidget(self.test_btn)

        self.tabs.addTab(main_widg, "Audio Files")
        
        top = QWidget()
        bottom = QWidget()
        tab3_layout.addWidget(top)
        tab3_layout.addWidget(bottom)
        
        top_layout = QVBoxLayout(top)
        # bottom_layout = QVBoxLayout(bottom)
        self.tab3_layout = top_layout
        
    def init_spectro(self):
        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(y=False)
        self.plot.setLabel('left', 'Frequenz', units='Hz')
        self.plot.setLabel('bottom', 'Zeit', units='m')
        self.plot.getViewBox().invertY(False)

        self.spectro_image = PGImage(self)
        self.plot.addItem(self.spectro_image)
                
        # self.plot.addColorBar( self.spectro_image, 
        #                        colorMap='viridis', values=(0, 1) )
        
        # # Get the colormap
        # # cmaps: https://matplotlib.org/stable/gallery/color/colormap_reference.html
        colormap = cm.get_cmap("cividis")  # cm.get_cmap("CMRmap")
        colormap = cm.get_cmap("inferno")
        colormap._init()
        # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
        lut = (colormap._lut * 255).view(np.ndarray)  
        # Apply the colormap
        self.spectro_image.setLookupTable(lut)

    def test(self):
        import bn_test 
        bn_test = reload(bn_test)
        bn_test.test(self)
        
    def reset_view(self):
        import bn_test 
        bn_test = reload(bn_test)
        bn_test.reset_view(self)
    
    def show_spectro(self):
        self.tab_plot.show() 
    

class PGImage(pg.ImageItem):
    def __init__(self, SV):
        super().__init__()
        self.SV = SV

    def mouseClickEvent(self, ev):        
        self.SV.audio.set_timeline(ev)
        
    def mouseDragEvent(self, ev): 
        if self.SV.cmd_key:
            return
        ev.accept()
        self.SV.audio.set_loop_rect(ev)
        
    def mouseMoveEvent(self, ev):
        #print(ev)
        if self.SV.cmd_key:
            ev.accept()
            pos = self.SV.audio.get_event_position(ev)
            return
            

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Main_Win()
    sys.exit(app.exec())
    
    



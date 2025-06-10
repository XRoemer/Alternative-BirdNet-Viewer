import pyqtgraph as pg

from PyQt6.QtWidgets import  QLabel, QVBoxLayout, QWidget, QTableWidget, QHBoxLayout
from PyQt6.QtWidgets import QTabWidget, QTableWidgetItem,QHeaderView
from pyqtgraph.Qt.QtCore import  QPointF, Qt
from pyqtgraph.Qt import QtCore

class SingleDetectionsWin(QWidget):

    def __init__(self,SV):
        super().__init__()
        
        self.SV = SV
        
        self.setWindowTitle("Details")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setGeometry(900, 200, 600, 600)
        
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)
        
        self.tab_table = QWidget()
        tab2_layout = QVBoxLayout(self.tab_table)

        self.table = QTableWidget()
        #self.table.setHorizontalHeaderLabels(["#", "Zeit (s)", "Länge (s)", "Confidence"])
        self.table.viewport().installEventFilter(self)
        tab2_layout.addWidget(self.table)

        # Buttons im Tab 2
        btn_layout2 = QHBoxLayout()
        tab2_layout.addLayout(btn_layout2)

        self.tabs.addTab(self.tab_table, "detected Birds")
        
    def eventFilter(self, source, event):
        if event.type() == 3: #MouseButtonRelease
            row = self.table.currentRow()
            col = self.table.currentColumn()
            
            files = self.SV.files
            cur_det = files.detections[files.current_file][files.cur_cfg_string]
            dets_overlapped = cur_det["det_birds_overlapped"]
            keys = list(dets_overlapped.keys())
            
            bird = list(dets_overlapped.keys())[col]
            entry = dets_overlapped[bird]["entries"][row]
            start = round(entry['start'],1)
            end = round(entry["end"],1)
            
            audio = self.SV.audio
            audio.loop_pos = [start,end]
            self.SV.plot.setXRange(start - 1, end + 1, padding=0)
            audio.timeline.setPos(start)
            audio.loop_pos_has_changed = True
            
        return QtCore.QObject.event(source, event)
        
          
    def create_table(self):

        cur_file = self.SV.files.current_file
        cur_cfg = self.SV.files.cur_cfg_string
        
        dets_overlapped = self.SV.files.detections[cur_file][cur_cfg]["det_birds_overlapped"]
        
        tab = self.table
        tab.setColumnCount(len(dets_overlapped))
        tab.setHorizontalHeaderLabels(dets_overlapped.keys())
        header = tab.horizontalHeader()  
         
        # for i in range(len(dets_overlapped)):    
        #     header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setRowCount(0)
        #self.text_items = {}
        
        set_item = self.table.setItem
        rowCount = self.table.rowCount
        
        entries = [len(x["entries"]) for x in dets_overlapped.values()]
        if len(entries) != 0:
            max_entries = max(entries)
        else:
            max_entries = 0
        for m in range(max_entries+1):
            tab.insertRow(tab.rowCount())
        
            
        i = 0  
         
        for name, dets in dets_overlapped.items():
            len_total = 0
            for nr,d in enumerate(dets["entries"]):
                start = d["start"]
                laenge = round(d["end"] - start,1)
                len_total += laenge
                coeff = round(d["coeff"],2)
                set_item(nr, i, QTableWidgetItem(f"{start} - {laenge}sec\n{coeff}"))
            
            set_item(max_entries, i, QTableWidgetItem(f"total {round(len_total,1)} secs"))
            i += 1
            
        for i in range(len(dets_overlapped)):    
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        tab.resizeRowsToContents()
    
    def clear(self):
        self.__init__(SV)
        self.create_table()
    
    
    
def test(SV):
    tab = SV.files_table
    item = tab.item(1,1)
    
    
    files = SV.files
    #files.save_detection_of_current_file(SV.files.current_file)
    
    # for i in dir(SV.files_table):
    #     print(i)
    
    item = SV.files_table.item(3,3)
    #cfg_string = item.text()
    
    det = files.detections[SV.files.current_file][cfg_string]
    
    x=0
    
    
    
def reset_view(SV):
    
    SV.plot.setYRange(0, 10000)
    SV.plot.setXRange(0, SV.audio.duration)





class Lines_and_Text():
    def __init__(self,SV):
        self.SV = SV
        self.wind = None
        self.init()
    
    def init(self):
        self.lines = {}
        self.positions = {x*300 + 2000 : ""  for x in range(100)}
        self.text_items = {}
        self.plot_items = []
        self.scene_items = []
        
        
    def create_line(self,name,sub,x1,x2,col="r"):
        
        posy = self.get_y_pos(name)
        #print(name,sub,x1)
        line = pg.PlotDataItem([x1, x2], [posy, posy], pen=pg.mkPen(col, width=2))
        
        if name not in self.lines:
            self.lines[name] = {}
            self.create_text_item_overlay(name,posy,col)
            
        self.lines[name][sub] = line
        self.SV.plot.addItem(line)
        self.plot_items.append(line)

    def set_line_pos(self,name,sub,data):
        x1,y1,x2,y2 = data
        self.lines[name][sub].setData([x1, x2], [y1, y2])
        
    def set_line_col(self,name,sub,col):
        line = self.lines[name][sub]
        pen = pg.mkPen(color=col, width=1)
        line.setPen(pen)
        return
    
    def get_y_pos(self,name):
        found = False
        for p,bird in self.positions.items():
            if name == bird:
                return p
        if not found:
            for p,bird in self.positions.items():
                if bird == "":
                    pos = p
                    found = True
                    self.positions[p] = name
                    break
            if found:
                return pos
            else:
                x=0
                raise Exception("no position found")
                return 0
                
    def clear(self):
        try:
            for item in self.plot_items:
                self.SV.plot.removeItem(item)
            for proxy in self.scene_items:
                self.SV.plot.scene().removeItem(proxy)
        except Exception as e:
            print(e)
        
        view = self.SV.plot.getViewBox()
        try:
            view.sigRangeChanged.disconnect()
        except Exception as e:
            #print(e)
            pass
        self.init()
 
    def create_bird_lines_on_spectro(self):
        self.clear()

        cols = ["red","yellow","LightGreen","LightBlue",
                "white","cyan","rosybrown","LightGreen","LightBlue",
                "white","cyan","DarkCyan","orange",
                "DarkGray","DarkGreen","DarkRed",
                "DarkCyan","red","green","blue","gray",
                "yellow","white",
                ]
        cols = cols + cols +cols +cols + cols + cols
        
        
        files = self.SV.files
        if files.current_file not in files.detections:
            return
        elif files.cur_cfg_string not in files.detections[files.current_file]:
            return
        
        
        dets = files.detections[files.current_file][files.cur_cfg_string]["det_birds_overlapped"]
        
        for nr, (birdname,vals) in enumerate(dets.items()):
            for entry in vals["entries"]:
                start = entry["start"]
                end = entry["end"]
                self.create_line(birdname,str(start),
                                  start,end,col=cols[nr])
        
        if self.wind == None:
            w = SingleDetectionsWin(self.SV)
            w.show()
            self.wind = w
        self.wind.create_table()


    def create_text_item_overlay(self,txt,y_pos,col):
        
        label = QLabel(txt)
        label.setStyleSheet(f"color: {col}; background-color: rgba(250, 250, 250, 0)")
        
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Maus durchlassen
        plot = self.SV.plot
        proxy = plot.scene().addWidget(label)
        
        label.adjustSize()
        view = plot.getViewBox()
        
        def update_text_positions(viewbox, range):
            x_range, y_range = range
            # Rechte obere Ecke in Datenkoordinaten
            x_max = x_range[1]
            # In Szene-Koordinaten umrechnen
            scene_pos = view.mapViewToScene(QPointF(x_max, y_pos))
            x = scene_pos.x() - label.width()
            p1 = view.mapViewToScene(QPointF(0, y_pos))
            label.move(int(x)-5,int(p1.y() - label.height() / 2))
    
        # Initial setzen
        update_text_positions(view,view.viewRange())
        
        # Bei Zoom/Pan Y-Position erhalten, X bleibt fix
        #view.sigYRangeChanged.connect(lambda vb, vr: update_text_positions())
        #view.sigRangeChanged.connect(lambda vb, vr: update_text_positions())
        view.sigRangeChanged.connect(update_text_positions)
        self.scene_items.append(proxy)


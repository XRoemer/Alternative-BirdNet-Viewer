from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QSpinBox, QDoubleSpinBox

class Settings():
    
    def __init__(self,SV):
        self.SV = SV
        
        #self.audio_input: str = ""
        #self.output: str | None = None
        self.min_conf: float = 0.25
        self.sensitivity: float = 1.0
        self.overlap: float = 0.0
        self.sf_thresh: float = 0.03
        self.merge_distance: float = 3.0
        #self.top_n: int | None = None
        #self.classifier: str | None = None
        self.lat: float = 53
        self.lon: float = 10
        self.week: int = 22
        #self.slist: str | None = None
        self.fmin: int = 0
        self.fmax: int = 15000
        #self.audio_speed: float = 1.0
        #self.combine_results: bool = False
        #self.rtype: Literal["table", "audacity", "kaleidoscope", "csv"] | list[Literal["table", "audacity", "kaleidoscope", "csv"]] = "table"
        #self.skip_existing_results: bool = False
        self.threads: int = 8
        self.batch_size: int = 1
        self.locale: str = "de"
        #self.additional_columns: list[str] | None = None
        
        self.create_settings()
        
    def create_settings(self):
        attributes = self.__dict__
        self.config = {}
        self.items = {}
        
        extract = [type(dict()),type(object())]
        
        for a,v in attributes.items():
            if type(v) in extract:
                continue
            elif str(type(v)) == "<class '__main__.SpectrogramViewer'>":
                continue
            else:
                #print(a,v)  
                line_widget = QWidget()
                self.SV.tab3_layout.addWidget(line_widget)
                line_layout = QHBoxLayout(line_widget) 
                line_layout.setSpacing(0)
                line_layout.setContentsMargins(0, 0, 0, 0) 
                label = QLabel(a)
                line_layout.addWidget(label)
                
                if type(v) == type(str()):
                    item = QLineEdit(str(v))
                elif type(v) == type(float()):
                    item = QDoubleSpinBox()
                    item.setValue(v)
                elif type(v) == type(int()):
                    item = QSpinBox()
                    item.setMaximum(15000)
                    item.setMinimum(-1)
                    item.setValue(v)
                    
                try:                
                    self.items[a] = item
                    if hasattr(item, "valueChanged"):
                        item.valueChanged.connect(self.receive_click)
                    else:
                        item.textChanged.connect(self.receive_click)
                    line_layout.addWidget(item)
                except Exception as e:
                    print(e)
                    pass
                self.config[a] = v
            pass
        
    
    def receive_click(self,ev):
        self.set_items_to_config()

        
    def set_items_to_config(self):
        items = self.items
        for s,item in items.items():
            if hasattr(item, "value"):
                val = item.value()
            else:
                val = item.text()
            self.config[s] = val
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
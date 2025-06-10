
from PyQt6.QtWidgets import QFileDialog,QTableWidgetItem,QHeaderView
from librosa import get_duration
from datetime import timedelta
import time, json
from labels_de import v_labels

class Files():
    def __init__(self,SV):
        
        self.SV = SV
        self.files_table = None # wird in create_files_tab gesetzt
        self.current_file = None
        self.files = {}
        self.detections = {}
        self.cur_cfg_string = ""
        

    def load_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self.SV, "WAV-Datei wählen", "", "Audio Files (*.wav);; mp3 (*.mp3)")
        
        for nr,f in enumerate(file_paths):
            self.files[nr] = {}
            self.files[nr]["full_path"] = f
            self.files[nr]["filename"] = f.split("/")[-1]
            self.files[nr]["detection"] = {}
            duration = get_duration(path=f)
            self.files[nr]["duration"] = str(timedelta(seconds=duration))
        
        if not file_paths:
            return
        
        self.fill_files_table()
        self.load_detetections()
        
    def fill_files_table(self):
        
        tab = self.files_table
        header = tab.horizontalHeader()  
        row_count = len(self.files)
        tab.setRowCount(row_count)
                
        set_item = tab.setItem
        rowCount = tab.rowCount

        for nr,file in self.files.items():
            set_item(int(nr), 0, QTableWidgetItem(f"{file['filename']}"))
            set_item(int(nr), 1, QTableWidgetItem(f"{file['duration']}"))
            set_item(int(nr), 2, QTableWidgetItem(f" "))

        for i in range(3):    
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        tab.resizeRowsToContents()
    
    
    def files_table_clicked(self, event):
        row = self.files_table.currentRow()
        col = self.files_table.currentColumn()
        tab = self.files_table
        
        if not tab.item(row,col):
            return
        elif col == 0:
            self.current_file = row
            self.set_current_file()
            #self.SV.lines.create_bird_lines_on_spectro()
        elif col == 2:
            sel = self.files_table.selectedItems()
            self.selected = list([s.row() for s in sel])
        elif col > 2:
            if not tab.cmd_key:
                #set detection to spetrogram
                self.cur_cfg_string = tab.item(row,col).text()
                if self.current_file == row:
                    self.SV.lines.clear()
                    self.SV.lines.create_bird_lines_on_spectro()
                else:
                    self.current_file = row
                    self.set_current_file()
                    self.SV.lines.create_bird_lines_on_spectro()
            else:
                # delete detection
                item = tab.item(row,col)
                cfg_string = item.text()
                tab.takeItem(row,col)
                del self.detections[row][cfg_string]      
            
    def set_current_file(self):
        filepath = self.files[self.current_file]["full_path"]
        # filepath gedoppelt - wieder herausnehmen
        self.SV.audio.file_path = filepath
        self.SV.audio.load_audio()
        self.SV.audio.set_spectrogram()
        self.SV.lines.clear()
        
 # ---------------------------------
    
    
    def create_detections(self):
        
        self.cur_cfg_string = self.get_cur_cfg_string()
        cfg_string = self.cur_cfg_string
        
        files = self.files
        paths = {nr:files[nr]["full_path"] for nr in self.selected}
        
        t0 = time.time()
        
        for nr, p in paths.items():
            det_orig = self.analyse(p)
            detection = self.reduce_detections(det_orig,nr)
            bird_det = self.create_bird_dict(detection,nr)
            det_birds_overlapped = self.find_overlapping_dets(bird_det,nr)
            
            if nr not in self.detections:
                self.detections[nr] = {}
            # wird ohne Nachfrage überschrieben - ändern?
            self.detections[nr][cfg_string] = {}
            self.detections[nr][cfg_string]["detections_orig"] = det_orig
            self.detections[nr][cfg_string]["detection"] = detection
            self.detections[nr][cfg_string]["bird_det"] = bird_det
            self.detections[nr][cfg_string]["det_birds_overlapped"] = det_birds_overlapped
            self.set_detection_to_table(nr,cfg_string)
            
        t1 = time.time()
        print(f"total recognition took {round(t1-t0,3)} sec")
            
    def set_detection_to_table(self,nr,cfg_string):
        tab = self.files_table      
        set_item = tab.setItem
        
        for i in range(20):
            tab_item = tab.item(nr, 3+i)
            if tab.item(nr, 3+i):
                if tab_item.text() == cfg_string:
                    print("detection already exists")
                    return
                else:
                    pass
            else:
                break
        
        set_item(nr, 3+i, QTableWidgetItem(cfg_string))
        #tab.resizeRowsToContents()
        
        
    def get_cur_cfg_string(self):
        config = self.SV.settings.config
        exclude = ["merge_distance","threads","batch_size","locale"]
        vals = [str(v) for k,v in config.items() if k not in exclude]
        cfg_string = "|".join(vals)   
        return cfg_string
        
    def analyse(self,path):
        t0 = time.time()
        
        config = self.SV.settings.config
        cfg = {k:v for k,v in config.items() if k != "merge_distance" }
        det = self.SV.birdnet_analyzer.analyze(path, **cfg)
        
        print(f"{time.time() - t0} secs")
        return det[0][1]
            
    def find_overlapping_dets(self,detections,nr):
        
        abstand = self.SV.settings.config["merge_distance"]
        
        new_bird_list = {}
        for bird,vals in detections.items():
    
            length = len(vals["start"])
            
            new_list = [{
                "start" : vals["start"][0],
                "end" : vals["end"][0],
                "coeff" : vals["coeff"][0],
                "len" : round(vals["end"][0] - vals["start"][0],2)
                }]
            
            new_list_count = 0
                        
            for i in range(length-1):
                
                start = vals["start"][i+1]
                end = vals["end"][i+1]
                coeff = vals["coeff"][i+1]
                
                new_list_end = new_list[new_list_count]["end"]
                
                if start < new_list_end + abstand:
                    new_list[new_list_count]["end"] = end
                    new_list[new_list_count]["coeff"] = max(new_list[new_list_count]["coeff"],coeff)
                    new_list[new_list_count]["len"] = round(end - new_list[new_list_count]["start"],2)
                else:
                    new_list.append({
                        "start" : start,
                        "end" : end,
                        "coeff" : coeff,
                        "len" : round(end-start,2)
                        }) 
                    new_list_count += 1
            
            lengths = [a["len"] for a in new_list]
                    
            new_bird_list[bird] = {}
            new_bird_list[bird] = {}
            new_bird_list[bird]["entries"] = new_list
            new_bird_list[bird]["tot_len"] = round(sum(lengths),1)
            
        
        # sort list on total length of detected entries
        new_bird_list = {i:v for i,v in sorted(new_bird_list.items(), 
                          key=lambda item:item[1]["tot_len"]
                          ,reverse = True
                          )}
                
        return new_bird_list
        
    def create_bird_dict(self,dic,nr):
        new_dic = {}
        for k,v in dic.items():
            time = k
            start,end = time.split("-")
            for entries in v:
                name = v_labels[entries[0].split("_")[0]]
                coeff = round(float(entries[1]),3)
                
                if name in new_dic:
                    new_dic[name]["start"].append(float(start))
                    new_dic[name]["end"].append(float(end))
                    new_dic[name]["coeff"].append(coeff)
                else:
                    new_dic[name] = {}
                    new_dic[name]["start"] = [float(start)]
                    new_dic[name]["end"] = [float(end)]
                    new_dic[name]["coeff"] = [coeff]
            
        return new_dic  
    
    def reduce_detections(self,det,nr):
        new_dic = {}
        for time,recog in det.items():
            if len(recog) != 0:
                new_dic[time] = recog
        return new_dic  
            
            
    def save_current_detection(self,cur_cfg_string = None, current_file = None):
        config = self.SV.settings.config
        detections = self.detections
        
        if cur_cfg_string == None:
            cur_cfg_string = self.cur_cfg_string
        if current_file == None:
            current_file = self.current_file
            
        filename = self.files[current_file]["filename"]
      
        try:
            with open(f'detections/{filename}.json') as json_data:
                dic = json.load(json_data)
                json_data.close()
        except:
            # create file if it not exists
            with open(f'detections/{filename}.json', 'w') as fout:
                json.dump({}, fout, indent=4)
                dic = {}
 
        new_dic = {}
        for time,dets in detections[current_file][cur_cfg_string]["detection"].items():
            new_dic[time] = []
            for det in dets:
                bird = det[0]
                coeff = float(det[1])
                new_dic[time].append([bird,coeff])
                
        dic[cur_cfg_string] = new_dic
            
        with open(f'detections/{filename}.json', 'w') as fout:
            json.dump(dic, fout, indent=4)

        
    def save_all_detections(self):
        detections = self.detections 
        for nr, dets in detections.items():
            for config_str in dets.keys():
                self.save_current_detection(cur_cfg_string = config_str, current_file = nr)
            
        
        
    def load_detetections(self):
        
        filenames = [v["filename"] for v in self.files.values()]
        
        for nr, filename in enumerate(filenames):
            try:
                with open(f'detections/{filename}.json') as json_data:
                    dic = json.load(json_data)
                    json_data.close()
            except:
                #print(filename,"doesn't exist")
                continue
            
            if nr not in self.detections:
                self.detections[nr] = {}
            for cfg_string, dets in dic.items():
                if cfg_string in self.detections[nr]:
                    #print("detection exist")
                    pass
                else:
                    self.detections[nr][cfg_string] = {}
                    self.detections[nr][cfg_string]["detection"] = dets
                    
                    bird_det = self.create_bird_dict(dets,nr)
                    det_birds_overlapped = self.find_overlapping_dets(bird_det,nr)
                    
                    self.detections[nr][cfg_string]["bird_det"] = bird_det
                    self.detections[nr][cfg_string]["det_birds_overlapped"] = det_birds_overlapped
                    self.set_detection_to_table(nr,cfg_string)
    
    
    
    
    
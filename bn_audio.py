import soundfile as sf
import sounddevice as sd
sd.default.latency = 'low'
import numpy as np
import time
from scipy.signal import spectrogram
from scipy.signal import resample_poly

import pyqtgraph as pg
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QGraphicsRectItem,QFileDialog
from pyqtgraph.Qt.QtCore import QRectF


class Audio():
    def __init__(self,SV):
        
        self.SV = SV
        self.file_path = ""
        self.files = {}
        
        self.data = None 
        self.audio_extract = None 
        
        self.timeline = None
        self.play_position = 0.0
        self.loop_pos = [0,1] #loop position in sec
        self.loop_pos_has_changed = False
        self.loop_duration = 1
        self.loop_is_on = False
        self.duration = 0.0
        
        self.playing = False
        self.play_start_time = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_playback_line)


    def get_file_path(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self.SV, "WAV-Datei wählen", "", "Audio Files (*.wav);; mp3 (*.mp3)")
        
        for nr,f in enumerate(file_paths):
            self.files[nr] = {}
            self.files[nr]["full_path"] = f
            self.files[nr]["filename"] = f.split("/")[-1]
            self.files[nr]["detection"] = {}
        
        if not file_paths:
            return
        self.file_path = file_paths[0]
        
    def load_audio(self):
        # 1. Audio laden
        data, sr = sf.read(self.file_path)
        if data.ndim > 1:
            data = data.mean(axis=1)  # Stereo to Mono
            
        if sr > 48000:
            data = resample_poly(data, up=1, down=2)
            sr = 48000
        
        # Normalize audio channels to between -1.0 and +1.0
        data /= np.max(np.abs(data),axis=0)
            
        self.duration = len(data) / sr
        self.data = data
        self.audio_extract = data
        self.sr = sr
        self.loop_pos = [0,self.duration]

    def save_audio(self):
        #sf.write("output.wav", data, samplerate=44100) 
        pass  
        
    def create_audio_extract(self):
        start_sec, end_sec = self.loop_pos
        start_sample = int((start_sec+0.25) * self.sr)
        end_sample = int((end_sec + 0.25) * self.sr)
        clip = self.data[start_sample:end_sample]
        self.audio_extract = self.apply_fade(clip)
        
    def apply_fade(self,data, fade_time_ms=5):

        fade_samples = int(self.sr * fade_time_ms / 1000)
    
        # Erzeuge linearen Fade-Verlauf (kann auch z.B. sinusförmig sein)
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        fade_out = np.linspace(1.0, 0.0, fade_samples)
    
        # Mono
        if data.ndim == 1:
            data[:fade_samples] *= fade_in
            data[-fade_samples:] *= fade_out
        # Stereo
        elif data.ndim == 2:
            data[:fade_samples, :] *= fade_in[:, np.newaxis]
            data[-fade_samples:, :] *= fade_out[:, np.newaxis]
        else:
            raise ValueError("Audio-Array muss 1D oder 2D sein")
    
        return data
    
    def set_spectrogram(self):
        nperseg = 1024
        noverlap = nperseg / 2
        # 2. Spektrogramm berechnen
        f, t, Sxx = spectrogram(self.data, self.sr, nperseg=nperseg, noverlap=noverlap)
        Sxx_dB = 10 * np.log10(Sxx + 1e-10)  # in dB

        # 4. Spektrogramm darstellen (transponiert!)
        self.SV.spectro_image.setImage(Sxx_dB.T, levels=(Sxx_dB.min(), Sxx_dB.max()*1.50))

        # Berechne Schrittgrößen
        dx = t[1] - t[0]
        dy = f[1] - f[0]
        
        self.dx = dx
        self.dy = dy 
        
        #from pyqtgraph.QtGui import QTransform
        import pyqtgraph as pg
        # Transformiere Bild mit invertierter Y-Achse
        transform = pg.QtGui.QTransform()
        transform.scale(dx, dy)
        self.SV.spectro_image.setTransform(transform)
        self.SV.spectro_image.setPos(0, 0)

        # Achsenbereiche setzen
        self.SV.plot.setXRange(t[0], t[-1])
        self.SV.plot.setYRange(0, 10000) #self.sr/2)

        # 6. Zeitlinie zurücksetzen (falls vorhanden)
        self.timeline.setPos(0)
        

    def toggle_playback(self):
        if not self.file_path:
            print("no file")
            return

        if self.playing:
            self.playing = False
            self.SV.play_btn.setText("play")
            self.stop_playback()
            return

        self.playing = True
        self.SV.play_btn.setText("stop")
        self.start_playback()

    def start_playback(self):
        if self.data is not None:
            self.timeline.setPos(self.loop_pos[0])
            self.play_start_time = time.time() - self.timeline.x()
            
            if self.loop_pos_has_changed:
                self.create_audio_extract()
                self.loop_pos_has_changed = False
            
            sd.play(self.audio_extract, samplerate=self.sr)
            
            self.timer.start(8) # alle 8ms updaten
            
    def stop_playback(self):
        self.playing = False
        sd.stop()
        self.timer.stop()

    def update_playback_line(self):
        if self.play_start_time is not None:
            self.play_position = time.time() - self.play_start_time
            self.timeline.setPos(self.play_position)
            
            x1,y1,x2,y2 = self.SV.plot.viewRect().getCoords()
            width = x2-x1
            
            end_is_visible = x2 > self.duration
            play_pos_greater_half = self.play_position > width/2 + x1
            
            if end_is_visible:
                pass
            elif self.play_position < x1:
                self.SV.plot.setXRange(self.play_position,
                                       self.play_position + width)
            elif play_pos_greater_half:
                self.SV.plot.setXRange(self.play_position - width/2, 
                                       self.play_position + width/2, padding=0)
            #self.SV.plot.setXRange(elapsed - 10, elapsed + 10, padding=0)
            if self.play_position > self.loop_pos[1]:
                if self.loop_is_on:
                    pass
                else:
                    self.stop_playback()
    
    def set_loop_rect(self,ev):
        
        try:
            SV = self.SV
            pos = self.get_event_position(ev)
            
            if ev.start:        
                if SV.loop_view != None:
                    loop_view = SV.loop_view
                    SV.plot.removeItem(loop_view)
        
                h = round(ev.pos().y() * SV.audio.dy)
                
                loop_view = QGraphicsRectItem(QRectF(pos, 0, 1, h))
                loop_view.setPen(pg.mkPen(color='r', width=1))  # Roter Rand
                loop_view.setBrush(pg.mkBrush(255, 255, 255, 20))  # Rote Füllung, alpha=100
            
                SV.loop_view = loop_view
                SV.plot.addItem(SV.loop_view)
                SV.audio.loop_pos = [pos,pos+1]
                
            if ev.finish:
                SV.audio.loop_pos[1] = pos
                self.loop_pos_has_changed = True
                SV.audio.timeline.setPos(SV.audio.loop_pos[0])
                SV.audio.toggle_playback()
                 
            else:
                loop_view = SV.loop_view  
                rect = loop_view.rect()
                rect.setRight(pos)
                h = round(ev.pos().y() * SV.audio.dy)
                rect.setBottom(h)
                loop_view.setRect(rect)
        except Exception as e:
            print(e)
        
        #self.timeline.setPos(pos)
    
    def get_event_position(self,ev):
        x = ev.pos().x()
        width_pwin = self.SV.spectro_image.image.shape[0]
        pos = round(x / width_pwin * self.duration,2)
        return pos
    
    def set_timeline(self,ev):
        pos = self.get_event_position(ev)
        self.timeline.setPos(pos)
        
        SV = self.SV
        if SV.loop_view != None:
            lv = SV.loop_view
            SV.plot.removeItem(lv)
            
        if self.playing:
            self.toggle_playback()
        
        self.loop_pos = [pos,self.duration]    
        self.loop_pos_has_changed = True
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
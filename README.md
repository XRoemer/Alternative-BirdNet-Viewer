# Compare BirdNet Detections
simple and quick comparisons between bird detections of the BirdNet-Analyzer with different settings  



tested on win11, python 3.11 and birdnet_analyzer 2.0.0  



## Installation
Besides the prerequisites for birdnet_analyzer it needs:
PyQt6, pyqtgraph, soundfile, sounddevice and librosa  

Download the BirdNET-Analyzer from here:
https://github.com/birdnet-team/BirdNET-Analyzer/releases/tag/v2.0.0  
Unpack and put the folder inside python/Lib/site-packages

Comment out the save command in Line 128 of the file **birdnet_analyzer/analyze/core.py**  
**\# save_analysis_params(os.path.join(cfg.OUTPUT_PATH, cfg.ANALYSIS_PARAMS_FILENAME))**  
and add:  
**return result_files[0]**  

## Usage
Run **bnv_main.py** from console or editor  
Open soundfiles (load audio)  
Mark the files to be analyzed in the **detect** column  
Files will be analyzed with the current settings. The settings are equivalent to the ones of the BirdNet-Analyzer except the **merge_distance**.  
Detections with smaller time distances than the merge_distance are summarized.  
**cmd-lmb** to delete a detection  

By clicking on detections in the file-window the corresponding spectrogram and detections windows will be opened.  
Clicking on an entry of the detections will zoom-in the spectrogram.  

### Navigation inside the spectrogram
wheel or two fingers on trackpad: zoom x-axis  
shift + wheel/fingers: zoom y-axis  
cmd + click + drag: move on x-axis  

space or button to play/stop audio  
click to set transport  
click + drag-right to set section  







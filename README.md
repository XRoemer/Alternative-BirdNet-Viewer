# Compare BirdNet Detections
simple and quick comparisons between bird detections of the BirdNet-Analyzer with different settings  



tested on win11 and python 3.11



## Installation
besides the prerequisites for birdnet_analyzer it needs:
PyQt6, pyqtgraph, soundfile, sounddevice and librosa  

download the BirdNET-Analyzer from here:
https://github.com/birdnet-team/BirdNET-Analyzer/releases/tag/v2.0.0  
unpack and put the folder inside python/Lib/site-packages

comment out the save command in Line 128 of the file **birdnet_analyzer/analyze/core.py**  
**\# save_analysis_params(os.path.join(cfg.OUTPUT_PATH, cfg.ANALYSIS_PARAMS_FILENAME))**  
and add:  
**return result_files[0]**  





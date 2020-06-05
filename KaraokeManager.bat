@echo off
py -m pip install --upgrade pip
py -m pip install colorama
py -m pip install textdistance
py KaraokeManager.py "DataFilesPath=%~1" "KaraokeFilesPath=%~2" "MusicFilesPath=%~3"
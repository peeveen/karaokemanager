@echo off
py -m pip install --upgrade pip
py -m pip install colorama
py -m pip install textdistance
py KaraokeManager.py "KaraokeFilesPath=%~1" "MusicFilesPath=%~2"
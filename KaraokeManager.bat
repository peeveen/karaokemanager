@echo off
REM Run this batch file with one argument: the path to the config YAML file.
py -m pip install --upgrade pip
py -m pip install colorama
py -m pip install pyyaml
py -m pip install textdistance
py KaraokeManager.py "%~1"
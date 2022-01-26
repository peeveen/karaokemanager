# Karaoke Manager

Command-line karaoke session management utility.

![KaraokeManager1](/media/karaokeManagerScreenshot1.png?raw=true)

![KaraokeManager2](/media/karaokeManagerScreenshot2.png?raw=true)

- Maintains a list of singers and their selected songs, key changes, etc.
- Easily add/delete/move singers and songs with short, simple commands. No mouse required.
- Fast undo & redo functionality for fat finger syndrome.
- Singers maintain their position in the queue, even if they currently have no songs cued up.
- Heavy OCD rating.
  - Enforces correctly formatted karaoke and music filenames.
  - Can analyze your library for duplicates, bad capitalization, similar-looking titles, missing "The" prefixes, etc (lists of analysis exemptions can be created).
- Writes the current list of singers to a file that you can display on-screen using software of your choice (for example, [Rainmeter](https://github.com/rainmeter/rainmeter)).
- Also has functionality and commands relating to cueing-up background music.
- Has been used in real life!

# Installation

Just run `pip install karaokemanager`.

# To run it

- First, install a driver! (see below)
- Copy the [YAML template](.template.yaml) to `.yaml`, and modify it with your own settings.
- Then just run `karaokemanager` or `py -m karaokemanager`
- Type `help` or `h` at the command line to get a list of available commands.

If you hate the config filename, rename it, and provide it as an argument to the program, e.g. `py -m karaokemanager renamed_file.yml`

# Drivers

This utility was created so that it could work with any karaoke player. For it to "drive" the player, you need to provide it with a driver.

Currently, one driver exists, for Winamp, the 90s music player for Windows. There are currently no drivers for any Linux apps, and if you know
of a useable Linux karaoke app, I'm all ears.

Anyway, if you want to use the Winamp driver, you should install it first with `pip install karaokemanagerwinampdriver`.

- [PyPI link](https://pypi.org/project/karaokemanagerwinampdriver/)
- [GitHub link](https://github.com/peeveen/karaokemanagerwinampdriver)

If you want to create a driver for your favourite karaoke player, create a Python class that exposes two methods:

```
def __init__(self, config)
def play_karaoke_file(self, karaoke_file, key_change, errors)
```

- `config` is the [pyyaml](https://github.com/yaml/pyyaml) object that represents the driver-specific section from the YAML config file.
- `karaoke_file` is the path to the file that should be played
- `key_change `is a numeric value that tells you how many semitones the pitch of the track should be shifted.
- `errors` is a list to which you should append any error messages that KaraokeManager will display to the user.
- The constructor should raise an exception if there is a problem.

Create a package containing this code, install it, and then set the driver->class value in the YAML config file to point to your class.

# Output files

On startup, and during runtime, Karaoke Manager will create a number of text files in your configured `tempDataPath`, many of which are intended to be of some use if you are skilled with scripting or configuring third-party software to do your bidding. If that's you, then some of the files which might be of interest are:

- `KaraokeManager.singers.txt` contains the names from the current queue of singers (one per line). If a singer has no songs cued up, their name is prefixed with a tab.
- `KaraokeManager.backgroundMusic.txt` is a file containing full paths of background music files (one per line). This is generated on startup by cross-referencing the contents of the `backgroundMusicPlaylistFilename` (as specified in your configuration) with the music files that are found in the `paths` that you have specified in the `music` section of the config. You may find this file useful as a playlist for a media player that you can fade in between singers.
- `KaraokeManager.musicRequests.txt` contains paths (one per line) of songs that you have selected with the `cue` command. You could write a script to monitor this file and deal with the request queue as you see fit.
- `KaraokeManager.songSuggestion.txt` is written to every ten seconds with the artist & title of a random track from your karaoke library. I use this to show a 'Why not try ...?' rolling display along the bottom edge of the karaoke screen.

# Scanning

On startup, Karaoke Manager will scan your karaoke and music paths for files. If it finds files that it doesn't like the look of, it'll let you know, and it will also write various reports to files in `dataPath` for you to examine at your leisure.

You can also ask Karaoke Manager to perform a deeper analysis of your files with the `scan` command. This command will analyse your files, looking for duplicates, bad casing, inconsistencies, etc. The `scan,quick` command will perform this basic checking, but `scan,all` will go a bit further and report similar-looking titles as potential duplicates.

To prevent false positives being reported, you can create lists of exemptions (one per line) in text files in `dataPath`:

- The scan will look for duet "reversals", meaning that if you have files by "Chas & Dave", but also some by "Dave & Chas", it'll flag them up. `ReversalExemptions.txt` can contain a list of those that are valid, with the two halves of the pair separated by a tab. Note that, currently, only an ampersand separator is considered.
- If the scan finds a file by an artist called, for example "The Greatest Band Ever", and also a file by an artist called "Greatest Band Ever", it will flag that up. `TheExemptions.txt` can prevent this by listing either of those values.
- The scan will nag you about words in filenames that are not capitalized. `LowerCaseExemptions.txt` can list those are valid (e.g. 'kd lang')
- The `all` scan will nag your about artists or titles that look very similar. `SimilarityExemptions.txt` can list those that should not be considered. Put both values on the same line, separated by a tab.

### Like It?

If you like this, and/or use it commercially, please consider throwing some coins my way via PayPal, at steven.fullhouse@gmail.com, or [buy me a coffee](https://www.buymeacoffee.com/peeveen).

### TODO

- More customization.
- More code comments.

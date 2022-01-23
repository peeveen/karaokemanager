# KaraokeManager

Command-line karaoke session management utility, driving Winamp.

![KaraokeManager1](/media/karaokeManagerScreenshot1.png?raw=true)

![KaraokeManager2](/media/karaokeManagerScreenshot2.png?raw=true)

- Maintains a list of singers and their selected songs, key changes, etc.
- Easily add/delete/move singers and songs with short, simple commands. No mouse required.
- Drives Winamp as the MP3/CDG player (so Windows-only for the moment).
- Operates Winamp [Pacemaker pitch changer plugin](https://www.surina.net/pacemaker/) via global hotkeys.
- Fast undo & redo functionality for fat finger syndrome.
- Singers maintain their position in the queue, even if they currently have no songs cued up.
- Heavy OCD rating.
  - Enforces correctly formatted karaoke and music filenames.
  - Can analyze your library for duplicates, bad capitalization, similar-looking titles, missing "The" prefixes, etc.
  - List of analysis exemptions can be created.
- Writes the current list of singers to a file for the [SingersQueue plugin](https://github.com/peeveen/gen_singersQueue) to display.
- Not just karaoke! There are also commands for adding non-karaoke music tracks to a playlist, for the [AutoDJ plugin](https://github.com/peeveen/gen_autoDJ) to play in-between singers.

# To run it

* Copy the [YAML template](KaraokeManagerConfig.template.yaml) to "KaraokeManagerConfig.yaml", and modify it with your own settings.
* Run `py KaraokeManager.py`
* If you hate the config filename, rename it, and provide it as an argument to the program, e.g. `py KaraokeManager.py renamed_file.yml`

### TODO

- Decouple Winamp, and allow for "modular" drivers for other KJ apps (and other platforms).
- More customization.
- More code comments.

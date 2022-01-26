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
- Writes the current list of singers to a file for the [SingersQueue plugin](https://github.com/peeveen/gen_singersQueue) to display.
- Not just karaoke! There are also commands for adding non-karaoke music tracks to a playlist, for the [AutoDJ plugin](https://github.com/peeveen/gen_autoDJ) to play in-between singers.

# Installation

Just run `pip install karaokemanager`.

# To run it

- First, install a driver! (see below)
- Copy the [YAML template](.template.yaml) to `.yaml`, and modify it with your own settings.
- Then just run `karaokemanager` or `py -m karaokemanager`
- If you hate the config filename, rename it, and provide it as an argument to the program, e.g. `py -m karaokemanager renamed_file.yml`

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

### Like It?

If you like this, and/or use it commercially, please consider throwing some coins my way via PayPal, at steven.fullhouse@gmail.com, or [buy me a coffee](https://www.buymeacoffee.com/peeveen).

### TODO

- More customization.
- More code comments.

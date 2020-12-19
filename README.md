
## Console braille graphics ELITE

![Screenshot](https://github.com/yope/cbgelite/blob/master/Documentation/screenshot.png)

This is an extremely lame attempt at doing graphics in a terminal window and on
top of that reimplement the classic BBC micro (and C64, etc...) game ELITE.
The original game (in case you don't know) was written in 1984 by Ian Bell and
David Braben for the BBC microcomputer. Read more about it [here](http://www.elitehomepage.org/).

### Prerequisites:

 * Python3
 * Python alsaaudio
 * Terminal program capable of displaying unicode and minimal 160x60 caracter size.
 * A mono-spaced font that contains braille characters in the same width as other characters.
 * Analog joystick or "flightstick" recommended.

Tested working combinations of terminal program and font:

 * Konsole with terminus TTF font
 * lxterminal with Inconsolata font.
 * gnome-terminal with Ubuntu Mono Bold.
 * gnome-terminal with Free Mono Bold (a bit stretched horizontally).

Notes:

 * You might want to change the color theme of your terminal program to improve contrast.
 * Bold fonts give better contrast. Ubunutu Mono Bold is one of the best looking.
 * Even running in a Linux virtual terminal (without any graphical environment) is
 possible if installing the 'console bralle' package. Note that this needs a tiny
 change in cbg.py to work properly and is not currently supported. Let me know if
 you want this.

### invocation

This game runs in a terminal, but a terminal program does not have support for
low level input events as they are required for such a game as this one.
Therefor this game needs access to the Linux input devices. Unfortunately a
reguar user does not have access to input devices directly, so you may need to
either add yourself to the "input" group on your machine, or run this game as
root (using sudo). Running as root is not really recommended, since most likely
you won't be able to access sound if pulse audio isn't configured to allow access
by other users than the one logged into the X/Wayland session.

There are two possible command-line options:

 * -fps: Run the title animation at maximum speed and display the achjieved FPS
   value in the top left of the screen.
 * -config: Start a rudimentary input config editor before the game starts, to
   reconfigure the input devices. You can assign joystick buttons or keyboard
   keys to the different functions. The configuration will be saved in the file
   "input_mapping.conf". This file is read if the game is started without this
   option.

### How to play the game

#### Configuring input devices

This is currently a work in progress, but you can try out the game if you want.
Currently you can fly around, hyperspace to another system and get into a fight
with enemy ships. The trading engine isn't implemented yet, and you cannot buy
any equipment for your Cobra MK-III... not even fuel.

The first thing you might probably want to do is configure your input devices.
You can either play with keyboard or joystick or a combination of both.

```bash
./elite.py -config
```

You will be asked a few questions about your input configuration. If you start
the game with a joystick connected, it will be detected and the game assumes you
want to use it. If no joystick is connected, the game assumes keyboard only mode.
Please note: If you have configured the game for joytick mode and then start it
with no joystick connected, it will not work. You will need to either connect your
joystick first, or re-configure the input devices.

This game does not use any external library for python except pyalsaaudio. For
this reason, joystick calibration is done every time when starting the game. If
you have a "flight stick", place it on a level surface and leave it centered when
starting the game. The game will also instruct you to do so.

This game has been tested with a "Speedlink Phantom Hawk Flight Stick". It can use
the two main axis for roll and pitch, the throttle lever and any combination of
buttons for fire, missile-lock, missile-launch, jump, hyperspace, ECM, etc...

**NOTE:** If you have a laptop with an external keyboard connected, you might need
to figure out wich one works. This game currently can use only one keyboard device,
and will use the first one it finds, which is likely the internal keyboard of your
laptop.

#### Audio output

This game uses pyalsaaudio directly to produce sound. At startup a simple analog
synthesizer in the game engine is used to render all the different sound samples.
If you are running pulse audio, this should be detected and used. If not, the game
just choses the "default" sound card configured.

#### Playing the game

Once the input devices are configured, start the game like this:

```bash
./elite.py
```
Sound samples are generated and the joystick calibration is performed. Hit SPACE
to start the game. You will be presented with the classic Cobra MK-III space ship
spinning in front of you. Press ESC to go to the game menu.

The first screen you will see is the status screen. You can press the keys 2...0
on your keyboard to select the different menu screens, or press 1 to launch from
the space station.

Currently working screens:

 * [4] Equip Ship
 * [5] Galactic Chart
 * [6] Short Range Chart
 * [7] Data on target system
 * [9] Status screen

Use the short range chart to select a target system (use configured roll/pitch
controls to move the cursor). The cicrle indicates the range of your current fuel
level. You cannot directly get to a system that is outside of this circle.
The press [7] to view some interesting data on the
selected planet. You can also access most of these screens while flying.

Press [1] to launch from the space station of the planet you start on (Lave).
Use the throttle to adjust speed, and you *roll* and *pitch* controls to maneuver
around. If you selected a target within fuel range, you can now press the
*Hyperspace* button and the countdown starts before you are transported to the
target system.

Once there, you will appear at a distance of the planet. You will see the target
planet directly ahead of you. And if you look closely, you might be able to see
the space station in orbit around the planet. Flying towards the planet will take
time, even at maximum speed. This is what "Jumps" are for. Press the *Jump*
button to dash closer to the planet. Currently you will be able to use the
*jump* button at any time while not too close to the plant or station. This will
not always be the case. In the original game, you cannot *jump* if any other
objects are close.

Once in a while you will see some asteroids or other space rocks appearing in
front of you. Als some enemy ships might appear and probably try to attack you
right away. Currently there is only one rather simple AI for other ships. Other
ships will just intermittently come flying at you and shooting when you are in
their target area, fly away from you if they got too close, or just make some
random turns.

If you manage to kill an enemy ship, it might leave some cargo cannisters floaring
around. Currently you can only either leave them clutter space, or shoot them.

#### Docking

Ah, yeah. Docking. This has always been the trauma of every beginning Elite player.
There are no docking computers in this game yet, so you have to hone those docking
skills!

At this moment the entrance to the space station is facing away from where you
approach it initially, instead of facing towards the planet. Will be fixed later.

The space station is rotating slowly around its Z-axis. you will need to align
your space ship with the station in such a way that the entrance is in front of
you and horizontally alighned. For succesful docking, try to fly towards the
entrance as perpendicular to the top surface as possible. Too much of an angle
will make you crash into the space station. Try to adjust your rolling speed
such that it matches the station. Try to keep the entrance as horizontal as
possible and accelerate a bit toward the station. If successful you will see
the docking sequence and be presented the status screen.

### Copying ###

All source files, except "chargen.rom" and "all_ships.ship" may be distributed
under the terms and conditions of the GPL version 2 license.

The ship data is extracted from the source code of "Elite The New Kind" as published
here on github: https://github.com/fesh0r/newkind

The "Elite The New Kind" repository and files don't contain any license, so
it is possibly not allowed to distribute them.

The ship data and the original game are Copyright by Ian Bell, David Braben
and/or Acornsoft in 1984.

The file "chargen.rom" contains a data dump from the Commodore C64 character
generator ROM, which is probably copyrighted and may not be distributed. OTOH,
there are numerous places where this file can be downloaded.

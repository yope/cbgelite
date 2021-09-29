
## Console braille graphics ELITE

![Screenshot](https://github.com/yope/cbgelite/blob/master/Documentation/screenshot.png)
![Screenshot](https://github.com/yope/cbgelite/blob/master/Documentation/short-range-map.png)
![Screenshot](https://github.com/yope/cbgelite/blob/master/Documentation/data-on-planet.png)
![Screenshot](https://github.com/yope/cbgelite/blob/master/Documentation/equip-ship.png)

This is an extremely lame attempt at doing graphics in a terminal window and on
top of that reimplement the classic BBC micro (and C64, etc...) game ELITE.
The original game (in case you don't know) was written in 1984 by Ian Bell and
David Braben for the BBC microcomputer. Read more about it [here](http://www.elitehomepage.org/).

### Prerequisites:

 * Python3
 * Cython3
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
 possible if installing the 'console braille' package. Note that this needs a tiny
 change in cbg.py to work properly and is not currently supported. Let me know if
 you want this.

### Building the cython extension

To build the cython modules, do this:

```bash
python3 setup.py build_ext --inplace
```

### Invocation

This game runs in a terminal, but a terminal program does not have support for
low level input events as they are required for such a game as this one.
Therefor this game needs access to the Linux input devices. Unfortunately a
reguar user does not have access to input devices directly, so you may need to
either add yourself to the "input" group on your machine, or run this game as
root (using sudo). Running as root is not really recommended, since most likely
you won't be able to access sound if pulse audio isn't configured to allow access
by other users than the one logged into the X/Wayland session.

There are two possible command-line options:

 * -fps: Show FPS and CPU load in the top right of the screen.
 * -config: Start a rudimentary input config editor before the game starts, to
   reconfigure the input devices. You can assign joystick buttons or keyboard
   keys to the different functions. The configuration will be saved in the file
   "input_mapping.conf". This file is read if the game is started without this
   option.

### How to play the game

#### Configuring input devices

This game is not entirely finished but already well playable. You can travel to
different systems, trade, earn bitcoins, equip your ship with extra stuff (like
fuel, extra cargo space, missiles, better laser cannons, E.C.M. system, etc...).

Basically like the original game. Among the few things that do not yet work are:
galactic hyperspace drive (so you can only stay on chart 1 out of 8), docking
computers, energy bomb, mining lasers, police attacking when fugitive, escape
capsules nor special missions.

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
If you are running pulseaudio, this should be detected and used. If not, the game
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

 * [1] Launch/front view
 * [2] Buy/Sell cargo
 * [4] Equip Ship
 * [5] Galactic Chart
 * [6] Short Range Chart
 * [7] Data on target system
 * [8] Price chart
 * [9] Status screen

Screens [2]...[4] are only available when docked in a space station.

Use the short range chart to select a target system (use configured roll/pitch
controls to move the cursor). The cicrle indicates the range of your current fuel
level. You cannot directly get to a system that is outside of this circle.
Then press [7] to view some interesting data on the
selected system. You can also access most of these screens while flying.

Pressing [2], you can buy or sell cargo at the current system market prices. To
buy one unit of cargo, highlight the item you want to buy from the menu by moving
the joystick or keyboard *ROLL* controls, then press the *FIRE* button.
To sell one unit of cargo, use either the *ARM MISSILE* or *FIRE MISSILE* button.

If you have enough money (Bitcoin) and want to buy some equipment for your ship,
press [4]. You will see a list of items available on the current system. Depending
on the Tech-Level of the current system, you may have more or less items available.
Highlight the item you want to add to your ship by using the *ROLL* controls.
Press the *FIRE* button to select. You will be either asked to confirm the
purchase by pressing *FIRE* a second time (or change to a different screen to
cancel), or in case of a laser cannon select the direction you want it to fire.
For example if you add extra pulse lasers to the *rear* of your ship, you will be
able to operate (fire) the laser cannon while looking out of the rear view.

Press [1] to launch from the space station of the planet you start on (Lave).
Use the throttle to adjust speed, and you *roll* and *pitch* controls to maneuver
around. If you selected a target system within fuel range, you can now press the
*Hyperspace* button and the countdown starts before you are transported to the
target system.

Once there, you will appear at a distance of the planet. You will see the target
planet directly ahead of you. And if you look closely, you might be able to see
the space station in orbit around the planet. Flying towards the planet will take
time, even at maximum speed. This is what "Jumps" are for. Press the *Jump*
button to dash closer to the planet. But beware of other ships appearing (specially
hunters or piracte ships when near a anarchic or feudal system), these will
prevent you from *jump*ing further. The message "Mass locked" will appear when
that happens.

Once in a while you will see some asteroids appearing in front of you.
Also some enemy ships might appear and probably try to attack you
right away.

If you manage to kill an enemy ship, it might leave some cargo cannisters floating
around. If your ship has *fuel scoops* fitted, you can pick them up if you fly at
them slowly (under 40% max speed), while maintaining them below your crosshairs.
You can then sell the cargo when docked at the station. Please beware that if your
ship is loaded to maximum cargo capacity, you will not be able to pick up any
cargo cannisters and instead collide with them, costing you some energy.

#### Missiles

If you have missiles fitted to your ship, you can fire them by first pressing the
*arm missile* button once. The missile is now armed and ready to acquire a target.
If you press the *arm missile* button a second time, the missile will be disarmed.
When a missile is armed, once you get a ship in your crosshairs, the missile will
lock target to that ship. Whenever you press the *fire missile* button, the missile
is launched and will home in on the locked target until it hits it.

In the same way, some enemy ships might launch a missile at you. If this happens,
and the missile hits you, your chances of survival are very slim.
To avoid being hit by a missile, you can shoot it down with your laser cannon, or
activate the *E.C.M.* system if fitted. When activating the *E.C.M.* system, all
flying missiles within radar range will be instantly destroyed... also yours if you
launched one.

#### Witch space

On very few occasions, a hyperspace jump to another system is interrupted in
*witch space*. Thargoid ships are able to intercept you during a hyperspace jump
and will attack you. Thargoids are touch to beat and may launch smaller Tharglets
(unmanned drones) to attack you from all sides. If you manage to kill the Thargoid
mother-ship, the Thatglets get deactivated and float aimlessly in space. In that
state, you can pick them up with your *fuel scoops*, if you have some cargo space
left.

If you manage to survive *witch space*, you are not automatically safe though.
There is no way to return to the system you come from, and you can only get to
a different system if you have enough fuel left. If not... you are doomed.

#### Docking

Ah, yeah. Docking. This has always been the trauma of every beginning Elite player.
There are no docking computers in this game yet, so you have to hone those docking
skills!

Like in the original game, the entrance to the docking station always faces
towards its planet.

The space station is rotating slowly around its Z-axis. you will need to align
your space ship with the station in such a way that the entrance is in front of
you and horizontally aligned. For succesful docking, try to fly towards the
entrance as perpendicular to the top surface as possible. Too much of an angle
will make you crash into the space station. Try to adjust your rolling speed
such that it matches the station. Try to keep the entrance as horizontal as
possible and accelerate a bit toward the station. If successful you will see
the docking sequence and be presented with the status screen.

### Copying ###

All source files, except "all_ships.ship" may be distributed under the terms
and conditions of the GPL version 2 license.

The ship data is extracted from the source code of "Elite The New Kind" as published
here on github: https://github.com/fesh0r/newkind

The "Elite The New Kind" repository and files don't contain any license, so
it is possibly not allowed to distribute them.

The ship data and the original game are Copyright by Ian Bell, David Braben
and/or Acornsoft in 1984.

The file "chargen.rom" is a copy of this file from the [MEGA64](https://github.com/MEGA65)
project:

 [chargen_pxlfont_2.3.rom](https://github.com/MEGA65/open-roms/blob/master/bin/chargen_pxlfont_2.3.rom)

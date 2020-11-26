
## Console braille graphics ELITE

![Screenshot](https://github.com/yope/cbgelite/blob/master/Documentation/screenshot.png)

This is an extremely lame attempt at doing graphics in a terminal window and on
top of that reimplement the classic BBC micro (and C64, etc...) game ELITE.

### Prerequisites:

 * Python3
 * Terminal program capable of displaying unicode and minimal 160x60 caracter size.
 * A mono-spaced font that contains braille characters in the same width as other characters.

Tested working combinations:

 * Konsole with terminus TTF font
 * lxterminal with Inconsolata font.

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

### Basic test mode operation

Currently the 3D engine has only some basic test code. A title screen is displayed,
with a rotating Cobra MK-III. If you press ESC, you get into the flight simulator.
There are several objects arranged in space, and you can fly around them.
There is a planet, with an orbiting coriolis space station in the distance and
a sun on the opposite side of you. Some enemy ships will fly around you and
get into attacking position. Their ability to shoot or even hit you is displayed
on the top of the screen, but no shots are actually fired yet.

The default controls with the keyboard are:

 * I,K: Pitch nose up down.
 * J,L: Roll left or right.
 * SPACE: Accelerate
 * Left-ALT: Brake
 * B: Short space jump
 * E: Activate ECM (not implemented yet)
 * M: Arm missile (not implemented yet)
 * N: Fire missile (not implemented yet)

All keys can be re-assigned if the "-config" option is used.
If a joystick is detected, it will be used. The config editor permits to assign
analog axis 3 of the joystick to the throttle optionally.

### Copying ###

All source files, except "chargen.rom" and "all_ships.ship" may be distributed
under the terms and conditions of the GPL version 2 license.

The ship data is extracted from the source code of "Elite The New Kind" as published
here on github: https://github.com/fesh0r/newkind

The "Elite The New Kind" repository and files don't contain any license, so
it is possibly not allowed to distribute them.

The file "chargen.rom" contains a data dump from the Commodore C64 character
generator ROM, which is probably copyrighted and may not be distributed. OTOH,
there are numerous places where this file can be downloaded.

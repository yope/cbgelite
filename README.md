
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

### Basic test mode operation

Currently the 3D engine has only some basic test code. A title screen is displayed,
with a rotating Cobra MK-III. If you press ESC, you get into the flight simulator.
There are 6 objects arranged in space, and you can fly around them.
There is one coriolis space station, which rotates slowly around its nose vector.
There are also two enemy ships flying around you changing attack strategies.

 * I,K: Pitch nose up down.
 * J,L: Roll left or right.
 * SPACE: Accelerate
 * Left-ALT: Brake

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

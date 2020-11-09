
## Console braille graphics ELITE

![Screenshot](https://github.com/yope/cbgelite/blob/master/Documentation/screenshot.png)

This is an extremely lame attempt at doing graphics in a terminal window and on
top of that reimplement the classic BBC micro (and C64, etc...) game ELITE.

### Prerequisites:

 * Python3
 * Terminal program capable of displaying unicode and minimal 160x60 caracter size.
 * A mono-spaced font that contains braille characters in the same with as other characters.

Tested working combinations:

 * Konsole with terminus TTF font
 * lxterminal with Inconsolata font.

### Basic test mode operation

Currently the 3D engine has only some basic test code. A title screen is displayed,
with a rotating Cobra MK-III. If you press ESC, you get into the flight simulator.
There are 6 objects arranged in space, and you can fly around them.
There is one coriolis space station, which rotates slowly around its nose vector.
There is also a second Cobra MK-III ship that also rolls constantly. The keybaord
controls work as follows:

 * I,K: Pitch nose up down.
 * J,L: Roll left or right.
 * W,S: Pitch the second cobra up or down (get close to it to observe).
 * SPACE: Accelerate
 * Left-ALT: Brake


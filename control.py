#
# Copyright (c) 2020 David Jander <djander@gmail.com>
#
# This file is part of CBGElite.
#
# CBGElite is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# CBGElite is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CBGElite.  If not, see <http://www.gnu.org/licenses/>.

from evdev import Input, find_devices
from time import sleep

class BaseDev:
	BTN_FIRE = 1
	BTN_MISSILE1 = 2
	BTN_MISSILE2 = 3
	BTN_ECM = 4
	def __init__(self):
		self.roll = 0.0
		self.pitch = 0.0
		self.throttle = 0.0
		self.btns = set()
		self.keys = set()

	def handle(self):
		pass

	def get_roll(self):
		return self.roll

	def get_pitch(self):
		return self.pitch

	def get_throttle(self):
		return self.throttle

	def get_buttons(self):
		return self.btns

	def get_keys(self):
		return self.keys

class Joydev(BaseDev):
	def __init__(self, jdev, kdev):
		super().__init__()
		self.jdev = jdev
		self.kdev = kdev
		self.axis_center = {}
		self.axis_max = {}
		self.axis_min = {}
		self.deadz = 15
		self.joymap = {
				288: self.BTN_FIRE,
				289: self.BTN_ECM,
				295: self.BTN_MISSILE1,
				296: self.BTN_MISSILE2,
			}

	def calibrate(self):
		print("Calibrating joystick...")
		print("Leave joystick centered and press SPACE")
		while not 57 in self.keys:
			self.handle()
			sleep(0.05)
		self.axis_center = {i:v for i,v in self.axis.items()}
		# FIXME: Calibrate max and min also?

	def _normalize(self, axis, index):
		mid = self.axis_center.get(index, 128)
		ret = min(max(axis[index] - mid, -100), 100)
		if ret < 0:
			ret = min(0.0, ret + self.deadz)
		else:
			ret = max(0.0, ret - self.deadz)
		return ret / 100.0

	def handle(self):
		self.keys = self.kdev.keys_pressed()
		self.btns = {self.joymap[x] for x in self.jdev.keys_pressed() if x in self.joymap}
		self.axis = axis = self.jdev.axis
		if 0 in axis:
			self.roll = -self._normalize(axis, 0)
		if 1 in axis:
			self.pitch = -self._normalize(axis, 1)
		if 3 in axis:
			self.throttle = (255 - axis[3]) / 255.0

class Kbddev(BaseDev):
	def __init__(self, kdev):
		super().__init__()
		self.kdev = kdev
		self.keymap = {} # FIMXE

	def handle(self):
		self.keys = keys = self.kdev.keys_pressed()
		self.btns = {self.keymap[x] for x in keys if x in self.keymap}
		if 57 in keys:
			self.throttle = min(self.throttle + 0.03, 1.0)
		if 56 in keys:
			self.throttle = max(self.throttle - 0.03, 0.0)
		if 23 in keys:
			self.pitch = min(self.pitch + 0.03, 1.0)
		elif 37 in keys:
			self.pitch = max(self.pitch - 0.03, -1.0)
		else:
			self.pitch = 0.0
		if 38 in keys:
			self.roll = max(self.roll - 0.03, -1.0)
		elif 36 in keys:
			self.roll = min(self.roll + 0.03, 1.0)
		else:
			self.roll = 0.0

class Control:
	def __init__(self, cbg):
		keyboard_dev, keyboard_name = find_devices()
		joystick_dev, joystick_name = find_devices(joystick=True)

		try:
			if keyboard_dev:
				self.keyboard = Input(keyboard_dev)
			else:
				self.keyboard = None
			if joystick_dev:
				self.joystick = Input(joystick_dev)
			else:
				self.joystick = None
		except PermissionError:
			print("""
There seems to be an issue with permissions, and I need your help.
Look, this game is a bare console program, and as unfortunate as it
seems, there is no way I can access an input device without some
extra priviledges. You basically have two choices to make this work:

 1.- Add yourself to the 'input' group so I can access the keyboard. or...
 2.- Try running this game with sudo.
""")
			self.cbg.exit(4)
		if self.joystick and self.keyboard:
			print("Found a joystick and a keyboard, defaulting to joystick mode")
			self.evdev = Joydev(self.joystick, self.keyboard)
		elif self.keyboard:
			self.evdev = Kbddev(self.keyboard)
		else:
			print("Joystick only option not supported yet... please connect a keyboard")
			cbg.exit(5)
		if self.joystick:
			self.evdev.calibrate()

	def get_evdev(self):
		return self.evdev

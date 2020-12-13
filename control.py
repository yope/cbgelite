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
import json

class BaseDev:
	BTN_UP = 0
	BTN_DOWN = 1
	BTN_LEFT = 2
	BTN_RIGHT = 3
	BTN_ACCELERATE = 4
	BTN_BRAKE = 5
	BTN_FIRE = 6
	BTN_MISSILE1 = 7
	BTN_MISSILE2 = 8
	BTN_ECM = 9
	BTN_JUMP = 10
	BTN_HYPERSPACE = 11
	def __init__(self):
		self.roll = 0.0
		self.pitch = 0.0
		self.throttle = 0.0
		self.btns = set()
		self.btns0 = set()
		self.keys = set()
		self.keys0 = set()
		self.keymap = {} # FIMXE
		self.joymap = {
				288: self.BTN_FIRE,
				289: self.BTN_ECM,
				295: self.BTN_MISSILE1,
				296: self.BTN_MISSILE2,
				299: self.BTN_JUMP
			}

	def set_mapping(self, mapping):
		self.joymap = {}
		self.keymap = {}
		for m in mapping:
			c, k, b = m
			if k is not None:
				self.keymap[k] = c
			if b is not None:
				self.joymap[b] = c

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

	def get_new_buttons(self):
		ret = self.btns - self.btns0
		self.btns0 = self.btns.copy()
		return ret

	def get_keys(self):
		return self.keys

	def get_new_keys(self):
		ret = self.keys - self.keys0
		self.keys0 = self.keys.copy()
		return ret

class Joydev(BaseDev):
	def __init__(self, jdev, kdev):
		super().__init__()
		self.jdev = jdev
		self.kdev = kdev
		self.axis_center = {}
		self.axis_max = {}
		self.axis_min = {}
		self.deadz = 15
		self.ascale = (100.0 + self.deadz) / 100.0
		self.throttle_axis = None

	def calibrate(self):
		print("Calibrating joystick...")
		print("Leave joystick centered and press SPACE")
		while not 57 in self.keys:
			self.handle()
			sleep(0.05)
		self.axis_center = {i:v for i,v in self.axis.items()}
		# FIXME: Calibrate max and min also?

	def set_throttle_axis(self, axis):
		self.throttle_axis = axis

	def _normalize(self, axis, index):
		mid = self.axis_center.get(index, 128)
		raw = axis[index] - mid
		if raw < 0:
			ret = min(0.0, raw + self.deadz)
		else:
			ret = max(0.0, raw - self.deadz)
		ret = min(max(ret * self.ascale, -100), 100)
		return ret / 100.0

	def _lpfilter(self, old, new):
		return (old * 0.8 + new * 0.2)

	def handle(self):
		self.keys = self.kdev.keys_pressed()
		self.btns = {self.joymap[x] for x in self.jdev.keys_pressed() if x in self.joymap}
		for k in self.keys:
			if k in self.keymap:
				self.btns.add(self.keymap[k])
		self.axis = axis = self.jdev.axis
		if 0 in axis:
			self.roll = self._lpfilter(self.roll, -self._normalize(axis, 0))
		if 1 in axis:
			self.pitch = self._lpfilter(self.pitch, -self._normalize(axis, 1))
		if self.throttle_axis and self.throttle_axis in axis:
			self.throttle = (255 - axis[self.throttle_axis]) / 255.0
		else:
			if self.BTN_ACCELERATE in self.btns:
				self.throttle = min(self.throttle + 0.03, 1.0)
			elif self.BTN_BRAKE in self.btns:
				self.throttle = max(self.throttle - 0.03, 0.0)

class Kbddev(BaseDev):
	def __init__(self, kdev):
		super().__init__()
		self.kdev = kdev

	def handle(self):
		self.keys = keys = self.kdev.keys_pressed()
		self.btns = {self.keymap[x] for x in keys if x in self.keymap}
		if self.BTN_ACCELERATE in self.btns:
			self.throttle = min(self.throttle + 0.03, 1.0)
		if self.BTN_BRAKE in self.btns:
			self.throttle = max(self.throttle - 0.03, 0.0)
		if self.BTN_UP in self.btns:
			self.pitch = min(self.pitch + 0.03, 1.0)
		elif self.BTN_DOWN in self.btns:
			self.pitch = max(self.pitch - 0.03, -1.0)
		else:
			self.pitch = 0.0
		if self.BTN_RIGHT in self.btns:
			self.roll = max(self.roll - 0.03, -1.0)
		elif self.BTN_LEFT in self.btns:
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
			cbg.exit(4)
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

	def get_yes_no(self):
		while True:
			k = self.keyboard.keys_pressed().copy()
			if 21 in k or 49 in k:
				break
			sleep(0.05)
		while self.keyboard.keys_pressed():
			sleep(0.05)
		if 21 in k:
			return True
		return False

	def save_mapping(self, mapping, jthrottle):
		with open("input_mapping.conf", "w") as f:
			txt = json.dumps({
				"mapping": mapping,
				"use_joystick_throttle": jthrottle
			})
			f.write(txt)

	def load_mapping(self):
		with open("input_mapping.conf", "r") as f:
			txt = f.read()
			obj = json.loads(txt)
			self.evdev.set_mapping(obj["mapping"])
			if obj["use_joystick_throttle"]:
				self.evdev.set_throttle_axis(3)

	def edit_controls(self):
		ctrl = []
		jt = False
		if not self.joystick:
			ctrl.append(("Up", BaseDev.BTN_UP))
			ctrl.append(("Down", BaseDev.BTN_DOWN))
			ctrl.append(("Left", BaseDev.BTN_LEFT))
			ctrl.append(("Right", BaseDev.BTN_RIGHT))
		else:
			print("Joystick axis 0 is roll left right")
			print("Joystick axis 1 is pitch up down")
			print("Do you want to use the joystick for throttle? (y/n)", end="", flush=True)
			jt = self.get_yes_no()
			print("Y" if jt else "N")
			if jt:
				print("Joystick axis 3 is throttle")
		if not jt:
			ctrl.append(("Accelerate", BaseDev.BTN_ACCELERATE))
			ctrl.append(("Brake", BaseDev.BTN_BRAKE))
		ctrl.append(("Fire", BaseDev.BTN_FIRE))
		ctrl.append(("Arm missile", BaseDev.BTN_MISSILE1))
		ctrl.append(("Fire missile", BaseDev.BTN_MISSILE2))
		ctrl.append(("Activate ECM", BaseDev.BTN_ECM))
		ctrl.append(("Near space JUMP", BaseDev.BTN_JUMP))
		ctrl.append(("Hyperspace Jump", BaseDev.BTN_HYPERSPACE))
		m = []
		for c in ctrl:
			print("Press button or key for {}:".format(c[0]), end="", flush=True)
			while True:
				keys = self.keyboard.keys_pressed()
				if self.joystick:
					btns = self.joystick.keys_pressed()
				else:
					btns = set()
				if keys or btns:
					break
				sleep(0.05)
			if keys:
				k = keys.pop()
				b = None
				print(" Key code {}".format(k))
			else:
				b = btns.pop()
				k = None
				print(" Joystick button {}".format(b))
			m.append((c[1], k, b))
			while True:
				keys = self.keyboard.keys_pressed()
				if self.joystick:
					btns = self.joystick.keys_pressed()
				else:
					btns = set()
				if not keys and not btns:
					break
				sleep(0.05)
		self.evdev.set_mapping(m)
		if jt:
			self.evdev.set_throttle_axis(3)
		self.save_mapping(m, jt)

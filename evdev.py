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

import struct
import os
import fcntl
import platform
from time import sleep

class Input:
	def __init__(self, fname):
		s = struct.Struct("@LLHHi")
		self.rlen = s.size
		self.event_parser = s.unpack
		self.fd = open(fname, "rb")
		flags = fcntl.fcntl(self.fd.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self.fd.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
		self.pressed = set()
		self.axis = {}

	def read_event(self):
		evb = self.fd.read(self.rlen)
		if not evb:
			return None
		if len(evb) == self.rlen:
			tsec, tusec, typ, code, value = self.event_parser(evb)
			return tsec + (tusec / 1000000), typ, code, value
		else:
			return None

	def read_key(self):
		while True:
			ev = self.read_event()
			if ev is None:
				return None
			ts, typ, code, value = ev
			if typ == 1: #EV_KEY
				break
			if typ == 3: #EV_ABS
				self.axis[code] = value
		return code, value

	def test(self):
		a = repr(self.axis)
		k = None
		while True:
			keys = repr(self.keys_pressed())
			a1 = repr(self.axis)
			if a != a1 or k != keys:
				print(keys, a1)
				a = a1
				k = keys
			sleep(0.05)

	def keys_pressed(self):
		ev = self.read_key()
		if ev is not None:
			code, value = ev
			if value == 0:
				self.pressed.discard(code)
			else:
				self.pressed.add(code)
		return self.pressed

def find_devices(joystick=False):
	with open("/proc/bus/input/devices", "r") as f:
		lines = f.readlines()
	name = None
	handlers = None
	ev = None
	for l in lines:
		l = l.strip(" \r\n")
		if l.startswith("N: Name="):
			name = l.split("=",1)[-1]
		elif l.startswith("H: Handlers"):
			handlers = l.split("=",1)[-1].split()
		elif l.startswith("B: EV="):
			ev = l.split("=",1)[-1]
			if ((int(ev, 16) & 0x120003) == 0x120003 and not joystick) or (ev.endswith("1b") and joystick):
				if joystick and not "js0" in handlers:
					continue
				print("Found device: {}".format(name))
				print("Handlers: {}".format(repr(handlers)))
				for h in handlers:
					if h.startswith("event"):
						return "/dev/input/"+h, name
	return None, None

if __name__ == "__main__":
	fname, dname = find_devices(joystick=True)
	ih = Input(fname)
	ih.test()

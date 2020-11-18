#!/usr/bin/env python3
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

class ShipReader:
	def __init__(self, fname=None, lines=None):
		if fname:
			with open(fname, "r") as f:
				lines = f.readlines()
		self.vert = []
		self.edge = []
		self.face = {}
		self.norm = []
		self.optidx = 0
		self.optorder = [
				"can_on_demise",
				"target_area",
				None,
				None,
				None,
				"gun_vertex",
				"explosion_count",
				None,
				None,
				"bounty",
				None,
				"vis_dist",
				"max_energy",
				"max_speed",
				None,
				None,
				None,
				"weapons"
			]
		self.parse(lines)

	def parse(self, lines):
		for l in lines:
			l.strip(" \r\n")
			w = l.split()
			if len(w) == 0:
				continue
			w = [x.strip(', ') for x in w]
			if w[0] == "VERTEX":
				self.process_vert(w)
			elif w[0] == "EDGE":
				self.process_edge(w)
			elif w[0] == "FACE":
				self.process_face(w)
			elif w[0] == "EQUB" or w[0] == "EQUW":
				self.process_option(w)

	def process_vert(self, w):
		self.vert.append((int(w[1]), int(w[2]), int(w[3])))

	def process_edge(self, w):
		p0 = int(w[1])
		p1 = int(w[2])
		f0 = int(w[3])
		f1 = int(w[4])
		self.edge.append((p0, p1))
		self.face.setdefault(f0, []).append(len(self.edge)-1)
		self.face.setdefault(f1, []).append(len(self.edge)-1)

	def process_face(self, w):
		self.norm.append((int(w[1]), int(w[2]), int(w[3])))

	def process_option(self, w):
		if w[1].startswith("&"):
			val = int(w[1][1:], 16)
		elif w[1].startswith("%"):
			val = int(w[1][1:], 2)
		else:
			val = int(w[1])
		optname = self.optorder[self.optidx]
		self.optidx += 1
		if not optname:
			return
		if optname == "weapons":
			self.opt_missiles = val & 7
			self.opt_laser_power = val >> 3
		else:
			setattr(self, "opt_" + optname, val)

class AllShips:
	def __init__(self, fname):
		with open(fname, "r") as f:
			lines = f.readlines()
		self.ships = {}
		slines = []
		sname = None
		for l in lines:
			if l.startswith(".SHIP "):
				if sname and slines:
					self.ships[sname] = ShipReader(fname=None, lines=slines)
				sname = l.split(" ",1)[1].strip(" \r\n").replace(" ", "_").lower()
				slines = []
			else:
				slines.append(l)
		if sname and slines:
			self.ships[sname] = ShipReader(fname=None, lines=slines)

if __name__ == "__main__":
	s = ShipReader("cobra_mk3.ship")
	print(repr(s.vert))
	print(repr(s.edge))
	print(repr(s.face))
	print(repr(s.norm))

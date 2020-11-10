#!/usr/bin/env python3

class ShipReader:
	def __init__(self, fname=None, lines=None):
		if fname:
			with open(fname, "r") as f:
				lines = f.readlines()
		self.vert = []
		self.edge = []
		self.face = {}
		self.norm = []
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

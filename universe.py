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

class SeedProcessor:
	def __init__(self, seed):
		self.seed = [x for x in seed]
		self.fastseed = [0, 0, 0, 0]
		self.pairs = "..LEXEGEZACEBISOUSESARMAINDIREA.ERATENBERALAVETIEDORQUANTEISRION"
		self.pairs0 = "ABOUSEITILETSTONLONUTHNO" + self.pairs
		self.desc_list = {
			0x81: ["fabled", "notable", "well known", "famous", "noted"],
			0x82: ["very", "mildly", "most", "reasonably", ""],
			0x83: ["ancient", "\x95", "great", "vast", "pink"],
			0x84: ["\x9E \x9D plantations", "mountains", "\x9C", "\x94 forests", "oceans"],
			0x85: ["shyness", "silliness", "mating traditions", "loathing of \x86", "love for \x86"],
			0x86: ["food blenders", "tourists", "poetry", "discos", "\x8E"],
			0x87: ["talking tree", "crab", "bat", "lobst", "\xB2"],
			0x88: ["beset", "plagued", "ravaged", "cursed", "scourged"],
			0x89: ["\x96 civil war", "\x9B \x98 \x99s", "a \x9B disease", "\x96 earthquakes", "\x96 solar activity"],
			0x8A: ["its \x83 \x84", "the \xB1 \x98 \x99", "its inhabitants' \x9A \x85", "\xA1", "its \x8D \x8E"],
			0x8B: ["juice", "brandy", "water", "brew", "gargle blasters"],
			0x8C: ["\xB2", "\xB1 \x99", "\xB1 \xB2", "\xB1 \x9B", "\x9B \xB2"],
			0x8D: ["fabulous", "exotic", "hoopy", "unusual", "exciting"],
			0x8E: ["cuisine", "night life", "casinos", "sit coms", " \xA1 "],
			0x8F: ["\xB0", "The planet \xB0", "The world \xB0", "This planet", "This world"],
			0x90: ["n unremarkable", " boring", " dull", " tedious", " revolting"],
			0x91: ["planet", "world", "place", "little planet", "dump"],
			0x92: ["wasp", "moth", "grub", "ant", "\xB2"],
			0x93: ["poet", "arts graduate", "yak", "snail", "slug"],
			0x94: ["tropical", "dense", "rain", "impenetrable", "exuberant"],
			0x95: ["funny", "wierd", "unusual", "strange", "peculiar"],
			0x96: ["frequent", "occasional", "unpredictable", "dreadful", "deadly"],
			0x97: ["\x82 \x81 for \x8A", "\x82 \x81 for \x8A and \x8A", "\x88 by \x89", "\x82 \x81 for \x8A but \x88 by \x89", "a\x90 \x91"],
			0x98: ["\x9B", "mountain", "edible", "tree", "spotted"],
			0x99: ["\x9F", "\xA0", "\x87oid", "\x93", "\x92"],
			0x9A: ["ancient", "exceptional", "eccentric", "ingrained", "\x95"],
			0x9B: ["killer", "deadly", "evil", "lethal", "vicious"],
			0x9C: ["parking meters", "dust clouds", "ice bergs", "rock formations", "volcanoes"],
			0x9D: ["plant", "tulip", "banana", "corn", "\xB2weed"],
			0x9E: ["\xB2", "\xB1 \xB2", "\xB1 \x9B", "inhabitant", "\xB1 \xB2"],
			0x9F: ["shrew", "beast", "bison", "snake", "wolf"],
			0xA0: ["leopard", "cat", "monkey", "goat", "fish"],
			0xA1: ["\x8C \x8B", "\xB1 \x9F \xA2", "its \x8D \xA0 \xA2", "\xA3 \xA4", "\x8C \x8B"],
			0xA2: ["meat", "cutlet", "steak", "burgers", "soup"],
			0xA3: ["ice", "mud", "Zero-G", "vacuum", "\xB1 ultra"],
			0xA4: ["hockey", "cricket", "karate", "polo", "tennis"]
	}

	def rotl(self, x):
		bit7 = x & 0x80
		return (2 * (x & 0x7f)) + (bit7 >> 7)

	def twist(self, v):
		return (self.rotl(v >> 8) << 8) | self.rotl(v & 0xff)

	def next_galaxy(self, seed):
		return [self.twist(seed[0]), self.twist(seed[1]), self.twist(seed[2])]

	def tweak(self, seed):
		temp = (seed[0] + seed[1] + seed[2]) & 0xffff
		seed[0] = seed[1]
		seed[1] = seed[2]
		seed[2] = temp
		return seed

	def get_name(self, seed):
		lng = seed[0] & 0x40
		ret = ""
		for i in range(4):
			idx = 2 * ((seed[2] >> 8) & 0x1f)
			seed = self.tweak(seed)
			if not lng and i >= 3:
				continue
			ret += self.pairs[idx]
			ret += self.pairs[idx+1]
		ret = ret.replace(".", "")
		return ret

	def copy_seed(self):
		return [s for s in self.seed]

	def set_seed(self, seed):
		self.seed = seed

	def set_fastseed(self, a, b, c, d):
		self.fastseed = [a, b, c, d]

	def fast_rand(self):
		a, b, c, d = self.fastseed
		x = (2 * a) & 0xff
		acc = x + c
		if a > 127:
			acc += 1
		self.fastseed[0] = acc & 0xff
		self.fastseed[2] = x
		acc = (int(acc > 255) + b + d) & 0xff
		self.fastseed[1] = acc
		self.fastseed[3] = b
		return acc

	def make_goatsoup(self, source, psy):
		idx = 0
		ret = ""
		while idx < len(source):
			ch = source[idx]
			idx += 1
			c = ord(ch)
			if c < 0x80:
				ret += ch
			else:
				if c <= 0xa4:
					rnd = self.fast_rand()
					ret += self.make_goatsoup(self.desc_list[c][int(rnd >= 0x33) + int(rnd >= 0x66) + int(rnd >= 0x99) + int(rnd >= 0xcc)], psy)
				elif c == 0xb0:
					ret += psy.name
				elif c == 0xb1:
					name = psy.name
					if name[-1] == "e" or name[-1] == "i":
						name = name[:-1]
					ret += name + "ian"
				elif 0xb2:
					n = self.fast_rand() & 3
					for i in range(n):
						x = self.fast_rand() & 0x3e
						if self.pairs0[x] != '.':
							ret += self.pairs0[x]
						if i and (self.pairs0[x + 1] != '.'):
							ret += self.pairs0[x + 1]
				else:
					print("Bad char in data [%x]".format(c))
		return ret


class System:
	def __init__(self, sp):
		s = self.seed = sp.copy_seed()
		self.x = s[1] >> 8
		self.y = s[0] >> 8
		self.government = (s[1] >> 3) & 7
		self.economy = (s[0] >> 8) & 7
		if self.government <= 1:
			self.economy |= 2
		self.techlevel = ((s[1] >> 8) & 3) + (self.economy ^ 7) + (self.government >> 1)
		if self.government & 1:
			self.techlevel += 1
		self.population = 4 * self.techlevel + self.economy + self.government + 1
		self.productivity = ((self.economy ^ 7) + 3) * (self.government + 4) + self.population * 8
		self.radius = 256 * (((s[2] >> 8) & 0x0f) + 11) + self.x
		sp.set_fastseed(s[1] & 0xff, s[1] >> 8, s[2] & 0xff, s[2] >> 8)
		self.name = sp.get_name(s).lower().capitalize()
		self.description = sp.make_goatsoup("\x8F is \x97.", self)
		self.str_economy = ["Rich Industrial", "Average Industrial", "Poor Industrial", "Mainly Industrial",
				"Mainly Agricultural", "Rich Agricultural", "Average Agricultural", "Poor Agricultural"][self.economy]
		self.str_government = ["Anarchy", "Feudal", "Multi-gov", "Dictatorship",
				"Communist", "Confederacy", "Democracy", "Corporate State"][self.government]
		sp.set_seed(s)

	def __repr__(self):
		s = f'Economy: {self.str_economy}\n\nGovernment: {self.str_government}\n\n' + \
				f'Tech. Level: {self.techlevel + 1}\n\nPopulation: {self.population} Billion\n\n' + \
				f'Gross Productivity: {self.productivity} M CR\n\nAverage Radius: {self.radius} km\n\n' + \
				f'{self.description}\n'
		return s

class Universe:
	def __init__(self):
		self.seed = [0x5a4a, 0x0248, 0xb753]
		self.base = [s for s in self.seed] # Make copy
		self.sp = SeedProcessor(self.seed)
		self.galaxies = []
		for j in range(8):
			sg = self.sp.copy_seed()
			sl = []
			for i in range(256):
				syst = System(self.sp)
				sl.append(syst)
			self.galaxies.append(sl)
			self.sp.set_seed(self.sp.next_galaxy(sg))

	def get_system_by_index(self, galaxy, idx):
		return self.galaxies[galaxy][idx]

	def get_system_near(self, galaxy, x, y):
		g = self.galaxies[galaxy]
		x0 = x - 2
		x1 = x + 2
		y0 = y - 2
		y1 = y + 2
		for s in g:
			if x0 < s.x < x1 and y0 < s.y < y1:
				return s
		return None

	def test(self):
		g0 = self.galaxies[3]
		for i in range(256):
			s = g0[i]
			print(s.name, s.x, s.y, s.government, s.economy, s.techlevel, s.description)
		s = self.get_system_near(0, 21, 172)
		print(s.name, s.x, s.y, s.government, s.economy, s.techlevel, s.description)
		s = self.get_system_near(2, 171, 179)
		print(s.name, s.x, s.y, s.government, s.economy, s.techlevel, s.description)
		print(repr(s))


if __name__ == "__main__":
	u = Universe()
	u.test()

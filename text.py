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

class FontData:
	def __init__(self, fname):
		with open(fname, "rb") as f:
			self.fontdata = f.read()

	def getglyph(self, code):
		code ^= 256
		return self.font[code*8:code*8+8]

	def getchar(self, char):
		if isinstance(char, str):
			char = ord(char)
		if 0x20 <= char <= 0x3f:
			return self.getglyph(char)
		elif 0x40 <= char <= 0x5f:
			return self.getglyph(char)
		elif 0x60 <= char <= 0x7f:
			return self.getglyph(char - 0x60)

	def optimize(self, bitmasks):
		self.font = bytearray(b'\x00' * 8 * 512)
		f = self.font
		for c in range(512):
			blk = self.fontdata[c*8:c*8+8]
			idx = c * 8
			for y in range(4):
				b0 = blk[y]
				b1 = blk[y+4]
				bmsk = bitmasks[y]
				for x in range(4):
					bit00 = (b0 >> (7-x*2)) & 1
					bit01 = (b0 >> (6-x*2)) & 1
					bit10 = (b1 >> (7-x*2)) & 1
					bit11 = (b1 >> (6-x*2)) & 1
					if bit00:
						f[idx+x] |= bmsk[0]
					if bit01:
						f[idx+x] |= bmsk[1]
					if bit10:
						f[idx+x+4] |= bmsk[0]
					if bit11:
						f[idx+x+4] |= bmsk[1]

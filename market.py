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

import random

class Market:
	def __init__(self):
		self.price_table = [
				("Food",         19,  -2, "t", 6,   0x01), # 0
				("Textiles",     20,  -1, "t", 10,  0x03), # 1
				("Radioactives", 65,  -3, "t", 2,   0x07), # 2
				("Slaves",       40,  -5, "t", 226, 0x1f), # 3
				("Liquor/Wines", 83,  -5, "t", 251, 0x0f), # 4
				("Luxuries",     196,  8, "t", 54,  0x03), # 5
				("Narcotics",    235, 29, "t", 8,   0x78), # 6
				("Computers",    154, 14, "t", 56,  0x03), # 7
				("Machinery",    117, 6,  "t", 40,  0x07), # 8
				("Alloys",       78,  1,  "t", 17,  0x1f), # 9
				("Firearms",     124, 14, "t", 29,  0x07), # 10
				("Furs",         176, -9, "t", 220, 0x3f), # 11
				("Minerals",     32,  -1, "t", 53,  0x03), # 12
				("Gold",         97,  -1, "kg", 66, 0x07), # 13
				("Platinum",     171, -2, "kg", 55, 0x1f), # 14
				("Gem-stones",   45,  -1, "g", 250, 0x0f), # 15
				("Alien Items",  53,  15, "t", 192, 0x03)  # 16
			]

	def calc_price(self, bp, mask, econ, ef):
		randb = random.randrange(255)
		ret = (bp + (randb & mask) + econ * ef) & 255
		return ret * 0.04

	def calc_stock(self, bq, mask, econ, ef):
		randb = random.randrange(255)
		ret = (bq + (randb & mask) - econ * ef)
		ret = max(0, ret) % 64
		return ret

	def get_pricelist(self, econ):
		mkt = []
		for name, bp, ef, unit, bq, mask in self.price_table:
			price = self.calc_price(bp, mask, econ, ef)
			stock = self.calc_stock(bq, mask, econ, ef)
			mkt.append([name, price, stock, unit])
		return mkt

def contraband_score(cargo):
	return cargo.get("3", 0) + 2 * cargo.get("6", 0) + cargo.get("10", 0)

if __name__ == "__main__":
	m = Market()
	pt = m.get_pricelist(5)
	for name, price, stock, unit in pt:
		print("{:20s}: {:5.2f} Cr, available: {} {}".format(name, price, stock, unit))
	print("")
	pt = m.get_pricelist(0)
	for name, price, stock, unit in pt:
		print("{:20s}: {:5.2f} Cr, available: {} {}".format(name, price, stock, unit))
	print("")

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

import asyncio
import random

random.seed()

class BaseAi:
	MOVE_AWAY = 0
	MOVE_RANDOM = 1
	MOVE_TO = 2
	def __init__(self, obj):
		self.obj = obj
		self.g3d = obj.g3d
		self.cbg = obj.mv.cbg
		self.loop = asyncio.get_event_loop()
		self.task = self.loop.create_task(self.task())
		self.speed = 6
		self.roll = 0.0
		self.strat = self.MOVE_TO
		self.dist = 10000.0
		self.dn = 0.0
		self.task.add_done_callback(lambda fut: fut.result())

	def handle(self):
		o = self.obj
		g = self.g3d
		o.pos = o.scale_add(o.nosev, o.pos, self.speed)
		self.dist = g.distv(o.pos)
		hvec = g.normalize(tuple(-x for x in o.pos))
		dnu = g.dot(g.normalize(g.add(o.nosev, o.roofv)), hvec)
		dnd = g.dot(g.normalize(g.sub(o.nosev, o.roofv)), hvec)
		self.dn = g.dot(o.nosev, hvec)
		if self.dn > 0.95:
			canshoot = True
			cs = " can shoot"
		else:
			canshoot = False
			cs = ""
		p = 0.0
		r = self.roll
		if self.strat is self.MOVE_TO:
			if self.dn < 0.0:
				p = -0.01
			elif dnu > dnd:
				p = -0.02
			else:
				p = 0.02
		elif self.strat is self.MOVE_AWAY:
			if self.dn > -0.5:
				p = 0.01
		if r or p:
			o.local_roll_pitch(r, p)
		#self.cbg.log("dist: {:6.1f} dnu: {:5.2f} dnd: {:5.2f} dn: {:5.2f} strat={}".format(self.dist, dnu, dnd, self.dn, self.strat) + cs)

	async def task(self):
		o = self.obj
		while o.alive:
			await asyncio.sleep(0.1)
			x = random.random()
			if x > 0.9:
				self.roll = 0.02
			elif x < 0.1:
				self.roll = 0.02
			else:
				self.roll = 0.0
			if self.strat is self.MOVE_AWAY and self.dist >= 5000:
				self.strat = self.MOVE_TO
				self.speed = 8
			elif self.strat is self.MOVE_TO and self.dist <= 2000:
				self.strat = self.MOVE_AWAY
				self.speed = 12
			if self.dn > 0.975:
				self.obj.mv.set_flashtext(o.name + " can hit")
			elif self.dn > 0.95:
				self.obj.mv.set_flashtext(o.name + " can shoot")

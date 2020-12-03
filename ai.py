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
		self.max_speed = obj.ship.opt_max_speed / 2
		self.speed = self.max_speed / 2
		self.roll = 0.0
		self.randpitch = 0.0
		self.strat = self.MOVE_TO
		self.dist = 10000.0
		self.dn = 0.0
		self.task.add_done_callback(lambda fut: fut.result())

	def handle(self):
		o = self.obj
		g = self.g3d
		o.pos = o.scale_add(o.nosev, o.pos, self.speed)
		self.dist = g.distv(o.pos)
		if self.dist > 50000:
			self.obj.vanish()
			return
		hvec = g.normalize(tuple(-x for x in o.pos))
		self.dn = dn = g.dot(o.nosev, hvec)
		ds = g.dot(o.sidev, hvec)
		dr = g.dot(o.roofv, hvec)
		if self.dn > 0.95:
			canshoot = True
			cs = " can shoot"
		else:
			canshoot = False
			cs = ""
		p = 0.0
		r = self.roll
		if self.strat is self.MOVE_TO:
			if dn > ds and dn > dr:
				if dr > 0.0:
					p = -0.02
				else:
					p = 0.02
			elif ds > dn and ds > dr:
				r = 0.02
			elif dr > ds and dr > dn:
				p = -0.02
		elif self.strat is self.MOVE_AWAY:
			if self.dn > -0.5:
				p = 0.01
		else: # MOVE_RANDOM
			p = self.randpitch
			#self.cbg.log(o.name + " move random {:6.1f}".format(self.dist))
		if r or p:
			o.local_roll_pitch(r, p)
		#if o.name == "KRAIT":
		#	self.cbg.log("dist: {:6.1f} dn: {:5.2f} ds: {:5.2f} dr: {:5.2f} strat={}".format(self.dist, dn, ds, dr, self.strat) + cs)

	async def task(self):
		o = self.obj
		ts = 0
		while o.alive:
			await asyncio.sleep(0.1)
			x = random.random()
			if x > 0.9:
				self.roll = 0.02
			elif x < 0.1:
				self.roll = 0.02
			else:
				self.roll = 0.0
			if x > 0.98 and self.strat is self.MOVE_TO:
				self.strat = self.MOVE_RANDOM
				self.speed = self.max_speed
				ts = 0
			elif self.strat is self.MOVE_RANDOM and x < 0.3:
				self.strat = self.MOVE_TO
				self.speed = self.max_speed * 0.7
				ts = 0
			elif self.strat is self.MOVE_AWAY and self.dist >= 5000:
				self.strat = self.MOVE_TO
				self.speed = self.max_speed * 0.9
				ts = 0
			elif self.strat is self.MOVE_TO and self.dist <= 2000:
				self.strat = self.MOVE_AWAY
				self.speed = self.max_speed * 0.8
				ts = 0
			ts += 1
			if ts > 500:
				self.strat = self.MOVE_RANDOM
				speed = self.max_speed * 0.85
				ts = 0
			if self.strat is self.MOVE_RANDOM:
				self.roll = random.uniform(-0.06, 0.06)
				self.randpitch = random.uniform(-0.06, 0.06)
				await asyncio.sleep(0.2)
			if self.dn > 0.975 and self.dist < 30000:
				self.obj.mv.set_flashtext(o.name + " can hit")
				if x < 0.3:
					o.shoot(True)
			elif self.dn > 0.95 and self.dist < 25000:
				self.obj.mv.set_flashtext(o.name + " can shoot")
				if x < 0.2:
					o.shoot(False)

class CanisterAi:
	def __init__(self, obj):
		self.obj = obj
		rnd = random.uniform
		self.vec = (rnd(-1, 1), rnd(-1, 1), rnd(-1, 1))
		self.roll = rnd(-0.01, 0.01)
		self.pitch = rnd(-0.01, 0.01)
		self.speed = rnd(0.0, 0.6)

	def handle(self):
		o = self.obj
		o.local_roll_pitch(self.roll, self.pitch)
		o.pos = o.scale_add(self.vec, o.pos, self.speed)

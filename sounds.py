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

import alsaaudio
import random
import struct
import asyncio
from time import monotonic

class SoundPlayer:
	def __init__(self, loop):
		self.loop = loop
		pcms = alsaaudio.pcms()
		if "pulse" in pcms:
			device = "pulse"
		else:
			device = "default"
		self.channels = 2
		self.wordsize = 2
		self.periodsize = 256
		self.pcm = alsaaudio.PCM(mode=alsaaudio.PCM_NONBLOCK, device=device)
		self.pcm.setchannels(self.channels)
		self.pcm.setperiodsize(self.periodsize)
		self.pcmfd = self.pcm.polldescriptors()[0]
		self.framelen = self.channels * self.wordsize
		self.periodlen = self.periodsize * self.framelen
		self.busy = False

	def start_play(self, buf):
		self.buf = buf
		self.pos = 0
		self.play_handler()
		# NOTE: Although we write to the alsa pcm device, the POLL mask alsa
		# returns has POLLIN set instead of POLLOUT, so we need to add a reader.
		self.loop.add_reader(self.pcmfd[0], self.play_handler)
		self.busy = True

	def stop_play(self):
		self.loop.remove_reader(self.pcmfd[0])
		self.busy = False

	def play_handler(self):
		beg = self.pos
		end = beg + self.periodlen
		n = self.pcm.write(self.buf[beg:end])
		self.pos += n * self.framelen
		if self.pos >= len(self.buf):
			self.stop_play()

class ADSR:
	def __init__(self, delay, a, d, sl, st, r):
		self.delay = delay
		self.a = a
		self.d = d
		self.sl = sl
		if not sl:
			st = 0
			r = 0
		self.st = st
		self.r = r
		self.time = delay + a + d + st + r
		self.rate = 44100 # FIXME

	def nsamples(self, time):
		return int(self.rate * time)

	def process(self, buf):
		p = 0
		if self.delay:
			p = self.ramp(buf, 0, self.delay, 0.0, 0.0)
		if self.a:
			p = self.ramp(buf, p, self.a, 0.0, 1.0)
		if self.d:
			p = self.ramp(buf, p, self.d, 1.0, self.sl)
		if self.sl and self.st:
			p = self.ramp(buf, p, self.st, self.sl, self.sl)
		if self.r:
			p = self.ramp(buf, p, self.r, self.sl, 0.0)
		return buf

	def ramp(self, buf, start, duration, v0, v1):
		n = self.nsamples(duration)
		m = (v1 - v0) / n
		for t in range(n):
			i = t + start
			buf[i] = int(buf[i] * (v0 + m * t))
		return start + n

class SynthVoice:
	def __init__(self):
		self.rate = 44100 # FIXME
		self.maxamp = 20000

	def nsamples(self, time):
		return int(self.rate * time)

	def gen_square(self, fstart, fend, dc, adsr, noise=False, ac0=None):
		if noise:
			fstart *= 4
			fend *= 4
		pern = pern0 = self.rate / fstart
		hpern = pern * dc
		pern1 = self.rate / fend
		ntotal = adsr.nsamples(adsr.time) + 1
		perm = (pern1 - pern0) / ntotal
		pc = 0
		buf = []
		v = self.maxamp
		l0 = v
		l1 = -v
		for t in range(ntotal):
			if pc > hpern:
				buf.append(l0)
			else:
				buf.append(l1)
			pc += 1.0
			if pc > pern:
				pc -= pern
				pern = pern0 + t * perm
				hpern = pern * dc
				if noise:
					l0 = random.randint(-v, v)
					l1 = random.randint(-v, v)
		adsr.process(buf)
		if ac0 is not None:
			self.filter_lp(buf, ac0)
		return buf

	def filter_lp(self, buf, ac0):
		gain = 2/(1+ac0)
		xv1 = xv0 = 0
		yv1 = yv0 = 0
		for i in range(len(buf)):
			xv0 = xv1
			xv1 = buf[i] / gain
			yv0 = yv1
			out = xv0 + xv1 - yv0 * ac0
			yv1 = out
			buf[i] = out

	def render_s16le_2ch(self, buf, vol=1.0, pan=0.0):
		pack_into = struct.Struct('<hh').pack_into
		out = bytearray(4*len(buf))
		vl = min(1.0, 1.0-pan) * vol
		vr = min(1.0, 1.0+pan) * vol
		for i,v in enumerate(buf):
			pack_into(out, i*4, int(vl * v), int(vr * v))
		return out

	def mix_s16le_2ch(self, buf0, buf1, vol0=1.0, vol1=1.0, pan0=0.0, pan1=0.0):
		pack_into = struct.Struct('<hh').pack_into
		out = bytearray(4*len(buf0))
		vol0 /= 2
		vol1 /= 2
		vl0 = min(1.0, 1.0-pan0) * vol0
		vr0 = min(1.0, 1.0+pan0) * vol0
		vl1 = min(1.0, 1.0-pan1) * vol1
		vr1 = min(1.0, 1.0+pan1) * vol1
		for i, (v0, v1) in enumerate(zip(buf0, buf1)):
			pack_into(out, i*4, int(vl0 * v0 + vl1 * v1), int(vr0 * v0 + vr1 * v1))
		return out

	async def test(self, loop):
		s = SoundPlayer(loop)
		s2= SoundPlayer(loop)
		adsr = ADSR(0.0, 0.0, 0.2, 0.1, 0.05, 0.05)
		buf0 = self.gen_square(330.0, 55, 0.3, adsr, noise=True)
		buf1 = self.gen_square(330.0, 55, 0.3, adsr)
		while True:
			t0 = monotonic()
			out = self.mix_s16le_2ch(buf0, buf1, 1.0, 0.6, -0.2, 0.2)
			dt = monotonic() - t0
			print(repr(dt))
			out2 = self.mix_s16le_2ch(buf0, buf1, 1.0, 0.6, -0.8, 0.4)
			s.start_play(out)
			await asyncio.sleep(0.05)
			s2.start_play(out2)
			while s.busy:
				await asyncio.sleep(0.02)
			out = self.mix_s16le_2ch(buf0, buf1, 0.0, 1.0, -0.2, 0.2)
			s.start_play(out)
			while s.busy:
				await asyncio.sleep(0.02)
			out = self.mix_s16le_2ch(buf0, buf1, 0.6, 0.6, -0.2, 0.2)
			s.start_play(out)
			while s.busy:
				await asyncio.sleep(0.02)

class SoundFX:
	def __init__(self, loop=None):
		self.loop = loop or asyncio.get_event_loop()
		self.players = [
				SoundPlayer(self.loop),
				SoundPlayer(self.loop),
				SoundPlayer(self.loop)
			]
		self.synth = SynthVoice()
		self.generate_samples()

	def generate_samples(self):
		adsr = ADSR(0.0, 0.0, 0.2, 0.1, 0.05, 0.1)
		adsr_long = ADSR(0.0, 0.0, 0.3, 0.2, 0.1, 0.2)
		adsr_dlay = ADSR(0.20, 0.0, 0.2, 0.1, 0.1, 0.1)
		self.laser1 = self.synth.gen_square(440, 55, 0.35, adsr, ac0=-0.8)
		self.laser2 = self.synth.gen_square(330, 55, 0.5, adsr, ac0=-0.85)
		laser3 = self.synth.gen_square(880, 110, 0.5, adsr, ac0=-0.75)
		myhit = self.synth.gen_square(330, 110, 0.5, adsr, noise=True)
		shexp1 = self.synth.gen_square(110, 55, 0.5, adsr_long, noise=True)
		shexp2 = self.synth.gen_square(150, 110, 0.5, adsr_long, noise=True)
		self.exp_short = self.synth.mix_s16le_2ch(shexp1, shexp2, 0.8, 0.8, -0.5, 0.5)
		self.myshot = self.synth.mix_s16le_2ch(laser3, self.laser2, 0.6, 0.4, -0.5, 0.5)
		self.myhit = self.synth.mix_s16le_2ch(laser3, myhit, 0.6, 1.0, -0.3, 0.3)
		self.laser_long = self.synth.gen_square(440, 55, 0.35, adsr_long, ac0=-0.3)
		self.damage = self.synth.gen_square(660, 110, 0.5, adsr_dlay, noise=True, ac0=-0.94)
		adsr_j1 = ADSR(0.0, 2.0, 0.0, 1.0, 0.0, 0.0) # Frist 2 seconds
		adsr_j2 = ADSR(0.0, 0.0, 0.0, 1.0, 4.0, 0.0) # Middle 4 seconds
		adsr_j3 = ADSR(0.0, 0.0, 2.0, 0.0, 0.0, 0.0) # Last 2 seconds
		adsr_jabrt = ADSR(0.0, 0.0, 1.0, 0.0, 0.0, 0.0) # Mass lock break
		j11 = self.synth.gen_square(55, 220, 0.5, adsr_j1, noise=True)
		j12 = self.synth.gen_square(220, 220, 0.5, adsr_j2, noise=True)
		j13 = self.synth.gen_square(220, 55, 0.5, adsr_j3, noise=True)
		j21 = self.synth.gen_square(33, 330, 0.1, adsr_j1, noise=True)
		j22 = self.synth.gen_square(330, 330, 0.1, adsr_j2, noise=True)
		j23 = self.synth.gen_square(330, 33, 0.1, adsr_j3, noise=True)
		j1abrt = self.synth.gen_square(220, 55, 0.5, adsr_jabrt, noise=True)
		j2abrt = self.synth.gen_square(330, 33, 0.1, adsr_jabrt, noise=True)
		self.jump1 = self.synth.mix_s16le_2ch(
				j11 + j12 + j13, j21 + j22 + j23, vol0=0.1, vol1=0.08, pan0=-0.5, pan1=0.5)
		self.jumpabrt = self.synth.mix_s16le_2ch(j1abrt, j2abrt, vol0=0.2, vol1=0.16, pan0=-0.5, pan1=0.5)
		adsr_exp1 = ADSR(0.0, 0.0, 2.0, 0.1, 2.0, 2.0)
		adsr_exp2 = ADSR(0.0, 0.0, 1.0, 0.1, 3.0, 2.0)
		exp1 = self.synth.gen_square(80, 50, 0.5, adsr_exp1, noise=True, ac0=-0.95)
		exp2 = self.synth.gen_square(220, 40, 0.5, adsr_exp2, noise=True, ac0=-0.92)
		self.exp = self.synth.mix_s16le_2ch(exp1, exp2, vol0=1.0, vol1=0.5, pan0=-0.2, pan1=0.2)
		launch1 = self.synth.gen_square(500, 500, 0.5, adsr_exp1, noise=True, ac0=-0.85)
		launch2 = self.synth.gen_square(400, 400, 0.5, adsr_exp2, noise=True, ac0=-0.87)
		self.launch = self.synth.mix_s16le_2ch(launch1, launch2, 1.0, 1.0, -0.5, 0.5)
		adsr_mlaunch = ADSR(0.0, 0.0, 1.0, 0.1, 0.4, 0.8)
		self.mlaunch1 = self.synth.gen_square(700, 800, 0.5, adsr_mlaunch, noise=True, ac0=-0.95)
		self.mlaunch2 = self.synth.gen_square(1000, 900, 0.5, adsr_mlaunch, noise=True, ac0=-0.96)
		adsr_hyp1 = ADSR(0, 0.3, 1.0, 0.5, 0.3, 1.0)
		hyper11 = self.synth.gen_square(110, 880, 0.5, adsr_hyp1, noise=True)
		hyper12 = self.synth.gen_square(2200, 8800, 0.3, adsr_hyp1)
		self.hyp1 = self.synth.mix_s16le_2ch(hyper11, hyper12, 0.5, 0.07, -0.3, 0.4)
		adsr_hyp21 = ADSR(0, 0.5, 0.0, 0.1, 0.1, 1.3)
		adsr_hyp22 = ADSR(0.35, 0.0, 0.5, 0.05, 0.5, 0.3)
		hyper21 = self.synth.gen_square(440, 880, 0.5, adsr_hyp21, noise=True)
		hyper22 = self.synth.gen_square(60, 30, 0.5, adsr_hyp22, noise=True, ac0=-0.985)
		self.hyp2 = self.synth.mix_s16le_2ch(hyper21, hyper22, 0.1, 1.0, 0.4, -0.1)
		self.beep = self.synth.render_s16le_2ch(
				self.synth.gen_square(880, 880, 0.45, ADSR(0, 0, 0.1, 0.6, 0.05, 0.1), noise=False, ac0=-0.85),
				vol=0.5)
		self.boop = self.synth.render_s16le_2ch(
				self.synth.gen_square(220, 220, 0.45, ADSR(0, 0, 0.1, 0.6, 0.05, 0.1), noise=False, ac0=-0.85),
				vol=0.5)
		ecm_sub_adsr = ADSR(0.0, 0.0, 0.02, 0.5, 0.03, 0.01)
		ecmttot = []
		ecmbtot = []
		t = 1
		for tfreq in range(1320, 720, -20):
			bfreq = tfreq / 3
			f = max(-1 + 1 / t, -0.997)
			t += 1
			ecmttot += self.synth.gen_square(tfreq, tfreq / 5, 0.3, ecm_sub_adsr, noise=False, ac0=f)
			ecmbtot += self.synth.gen_square(bfreq, bfreq / 4, 0.4, ecm_sub_adsr, noise=False, ac0=f)
		self.ecm = self.synth.mix_s16le_2ch(ecmttot, ecmbtot, 0.4, 0.4, -0.8, 0.8)

	def play_shot(self, pan=0.0):
		pan0 = max(-1.0, pan - 0.2)
		pan1 = min(1.0, pan + 0.2)
		buf = self.synth.mix_s16le_2ch(self.laser1, self.laser2, 0.1, 0.1, pan0, pan1)
		return self.play(buf)

	def play_myshot(self):
		return self.play(self.myshot)

	def play_myhit(self):
		return self.play(self.myhit)

	def play(self, buf, force=False):
		for p in self.players:
			if not p.busy:
				p.start_play(buf)
				return p
		if force:
			self.players[-1].start_play(buf)
			return self.players[-1]
		return None

	def play_hit(self, pan=0.0):
		pan0 = max(-1.0, pan - 0.2)
		pan1 = min(1.0, pan + 0.2)
		buf = self.synth.mix_s16le_2ch(self.laser_long, self.damage, 0.5, 1.0, pan0, pan1)
		return self.play(buf)

	def play_jump(self):
		return self.play(self.jump1)

	def play_jumpabort(self):
		return self.play(self.jumpabrt)

	def play_explosion(self):
		return self.play(self.exp, force=True)

	def play_short_explosion(self):
		return self.play(self.exp_short, force=True)

	def play_launch(self):
		return self.play(self.launch)

	def play_hyperspace_start(self):
		return self.play(self.hyp1, force=True)

	def play_hyperspace_end(self):
		return self.play(self.hyp2, force=True)

	def play_beep(self):
		return self.play(self.beep, force=True)

	def play_boop(self):
		return self.play(self.boop, force=True)

	def play_ecm(self):
		return self.play(self.ecm)

	def play_missile_launch(self, pan=0.0):
		pan0 = max(-1.0, pan - 0.2)
		pan1 = min(1.0, pan + 0.2)
		buf = self.synth.mix_s16le_2ch(self.mlaunch1, self.mlaunch2, 0.5, 0.5, pan0, pan1)
		return self.play(buf)

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	v = SynthVoice()
	loop.run_until_complete(v.test(loop))

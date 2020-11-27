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
		self.wordsize = 2
		self.rate = 44100 # FIXME
		self.maxamp = 20000

	def nsamples(self, time):
		return int(self.rate * time)

	def gen_square(self, fstart, fend, dc, adsr, noise=False):
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
		return buf

	def render_s16le_2ch(self, buf, pan=0.0):
		pack_into = struct.Struct('<hh').pack_into
		out = bytearray(4*len(buf))
		vl = min(1.0, 1.0-pan)
		vr = min(1.0, 1.0+pan)
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
		self.laser1 = self.synth.gen_square(440, 55, 0.35, adsr)
		self.laser2 = self.synth.gen_square(330, 55, 0.5, adsr)
		self.laser_long = self.synth.gen_square(440, 55, 0.35, adsr_long)
		self.damage = self.synth.gen_square(660, 110, 0.5, adsr_dlay, noise=True)

	def play_shot(self, pan=0.0):
		pan0 = max(-1.0, pan - 0.2)
		pan1 = min(1.0, pan + 0.2)
		buf = self.synth.mix_s16le_2ch(self.laser1, self.laser2, 0.1, 0.1, pan0, pan1)
		self.play(buf)

	def play(self, buf):
		for p in self.players:
			if not p.busy:
				p.start_play(buf)
				break

	def play_hit(self, pan=0.0):
		pan0 = max(-1.0, pan - 0.2)
		pan1 = min(1.0, pan + 0.2)
		buf = self.synth.mix_s16le_2ch(self.laser_long, self.damage, 0.5, 1.0, pan0, pan1)
		self.play(buf)

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	v = SynthVoice()
	loop.run_until_complete(v.test(loop))

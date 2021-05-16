#
# Copyright (c) 2021 David Jander <djander@gmail.com>
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

#cython: language_level=3

cimport cython
from libc.stdio cimport printf, fflush, stdout
from time import monotonic, process_time

cdef class ScreenDiff:
	cdef char * _cmap
	cdef char * _cmap0
	cdef char * _ccolormap
	cdef char * _ccolormap0
	cdef unsigned int _cwidth, _cheight
	cdef unsigned int _buflen
	cdef object _cmap_back, _cmap0_back
	cdef object _ccolormap_back, _ccolormap0_back
	cdef list _charcodes
	cdef bint _showfps
	cdef float _tscpu, _ts, _fps, _fpscount, _cpuload
	def __init__(self, cw, ch, showfps=False):
		self._showfps = showfps
		self._fps = 0.0
		self._cpuload = 0.0
		self._fpscount = 0.0
		self._tscpu = process_time()
		self._ts = monotonic()
		self._charcodes = [chr(x).encode("utf-8") for x in range(0x2800, 0x2900)]
		self._charcodes[0] = b' ' # Replace 0 with space. This is faster in some cases.
		cdef unsigned int size = cw * ch
		self._buflen = size
		self._cwidth = cw
		self._cheight = ch
		self._cmap_back = bytearray(b'\x00' * size)
		self._cmap0_back = bytearray(b'\x00' * size)
		self._cmap = <char *>self._cmap_back
		self._cmap0 = <char *>self._cmap0_back
		self._ccolormap_back = bytearray(b'\x00' * size)
		self._ccolormap0_back = bytearray(b'\x00' * size)
		self._ccolormap = <char *>self._ccolormap_back
		self._ccolormap0 = <char *>self._ccolormap0_back

	cpdef object _get_map(self):
		return self._cmap_back

	cpdef object _get_colormap(self):
		return self._ccolormap_back

	cpdef clearmap(self):
		cdef unsigned int i
		for i in range(self._buflen):
			self._cmap[i] = 0

	cpdef clearcolormap(self):
		cdef unsigned int i
		for i in range(self._buflen):
			self._ccolormap[i] = 0x0f

	@cython.cdivision(True)
	cdef void _show_stats(self):
		cdef double tscpu, ts, dcpu, dt
		if self._fpscount >= 100:
			tscpu = process_time()
			ts = monotonic()
			dcpu = tscpu - self._tscpu
			dt = ts - self._ts
			if dt > 0:
				self._fps = self._fpscount / dt
				self._cpuload = (100.0 * dcpu) / dt
			self._ts = ts
			self._tscpu = tscpu
			self._fpscount = 0
		else:
			self._fpscount += 1
		printf("\x1b[2;149HFPS:%5.1f", self._fps)
		printf("\x1b[3;149HCPU:%5.1f%%", self._cpuload)

	cpdef unsigned int full_redraw_screen(self):
		cdef char fg0 = 16
		cdef char bg0 = 16
		cdef char b, c, fg, bg
		cdef unsigned int curc = 256
		cdef unsigned int y, x, idx
		cdef char *u
		cdef unsigned int  count = 0
		for y in range(self._cheight):
			count += printf("\x1b[%d;1H", y+1)
			for x in range(self._cwidth):
				idx = y * self._cwidth + x
				b = self._cmap[idx]
				c = self._ccolormap[idx]
				if curc != <unsigned int>c:
					fg = c & 0x0f
					curc = c
					if fg0 != fg:
						fg0 = fg
						count += printf("\x1b[38;5;%dm", fg)
					bg = c >> 4
					if bg0 != bg:
						bg0 = bg
						count += printf("\x1b[48;5;%dm", bg)
				u = self._charcodes[b]
				count += printf("%s",u)
		if self._showfps:
			self._show_stats()
		fflush(stdout)
		return count

	@cython.cdivision(True)
	cpdef unsigned int redraw_screen(self):
		cdef char fg0 = 16
		cdef char bg0 = 16
		cdef char b, c, fg, bg
		cdef unsigned int i, x, y, x0 = 9999, y0 = 9999
		cdef char *u
		cdef unsigned int  count = 0
		for i in range(self._buflen):
			b = self._cmap[i]
			c = self._ccolormap[i]
			if self._cmap0[i] != b or self._ccolormap0[i] != c:
				self._cmap0[i] = b
				self._ccolormap0[i] = c
				y = i // self._cwidth
				x = i % self._cwidth
				fg = c & 0x0f
				bg = c >> 4
				u = self._charcodes[b]
				if x != x0 or y != y0:
					count += printf("\x1b[%d;%dH", y + 1, x + 1)
				if fg0 == fg and bg0 == bg:
					count += printf("%s", u)
				elif fg0 == fg and bg0 != bg:
					count += printf("\x1b[48;5;%dm%s", bg, u)
				elif fg0 != fg and bg0 == bg:
					count += printf("\x1b[38;5;%dm%s", fg, u)
				else:
					count += printf("\x1b[48;5;%dm\x1b[38;5;%dm%s", bg, fg, u)
				bg0 = bg
				fg0 = fg
				x0 = x + 1
				y0 = y
		fg = 15
		bg = 0
		if fg != fg0 or bg != bg0:
			count += printf("\x1b[48;5;%dm\x1b[38;5;%dm", bg, fg)
		if self._showfps:
			self._show_stats()
		fflush(stdout)
		return count

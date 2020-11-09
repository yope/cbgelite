
from math import sin, cos, sqrt, acos, pi

def normalize(v, tolerance=0.00001):
	mag2 = sum(n * n for n in v)
	if abs(mag2 - 1.0) > tolerance:
		mag = sqrt(mag2)
		v = tuple(n / mag for n in v)
	return v

def qmult(q1, q2):
	w1, x1, y1, z1 = q1
	w2, x2, y2, z2 = q2
	w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
	x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
	y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
	z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
	return w, x, y, z

def qconj(q):
	w, x, y, z = q
	return (w, -x, -y, -z)

def qvmult(q1, v1):
	q2 = (0.0,) + v1
	return qmult(qmult(q1, q2), qconj(q1))[1:]

def aangle2q(v, theta):
	v = normalize(v)
	x, y, z = v
	theta /= 2
	st = sin(theta)
	return cos(theta), x * st, y * st, z * st

def q2aangle(q):
	w, v = q[0], q[1:]
	theta = acos(w) * 2.0
	return normalize(v), theta

def rotate_aangle(p, v, theta):
	pi2 = pi * 2
	if abs(theta) >= pi2:
		theta = theta - int(theta / pi2) * pi2
	if theta == 0.0:
		return p
	return qvmult(aangle2q(v, theta), p)

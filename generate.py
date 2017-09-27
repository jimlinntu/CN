import random
with open("test_in", "w") as f:
	for i in range(1000):
		print >>f, str(random.randint(0,999999999999))

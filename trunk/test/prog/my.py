while 1:
	try:
		s = raw_input()
		a,b = map(int, s.split())
		print a+b
	except EOFError:
		import sys
		sys.exit(0)

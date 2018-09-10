with open('config.h', 'rt') as fin, open('config.h.stripped', 'wt') as fout:
	for line in fin:
		if '#' == line[0]:
			print(line)
			fout.write(line)

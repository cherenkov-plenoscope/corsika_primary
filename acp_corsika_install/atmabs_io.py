import numpy as np

EXTINCTION_SHAPE = (105, 41)


def read_atmabs_dat(path):
    table = []
    wavelength = []
    with open(path, 'rt') as fin:
        header = fin.readline()
        for line in fin:
            if line and line[0] != '\n':
                if line[0:4] != '    ':
                    wavelength.append(float(line))
                else:
                    sub = line
                    for i in range(5):
                        sub += fin.readline()
                    table.append(np.fromstring(sub, sep=' '))
    extinction = np.array(table)
    return {
        'wavelength': wavelength,
        'extinction': extinction
    }


def write_atmabs(path, atmabs):
    with open(path, 'wt') as fout:
        head = 'ATMOSPHERIC EXTINCTION COEFF. '
        head += 'FOR CERENKOV PHOTONS, 180-700nm, '
        head += 'in STEPS of km   \n'
        fout.write(head)
        for i, wvl in enumerate(atmabs['wavelength']):
            fout.write(' '+str(int(wvl))+'\n')
            s = 0
            for ext in atmabs['extinction'][i]:
                fout.write('    ')
                fout.write('{:>6.3f}'.format(ext))
                if s < 9:
                    s += 1
                else:
                    fout.write('\n')
                    s = 0
            fout.write('\n')
        fout.write('\n')

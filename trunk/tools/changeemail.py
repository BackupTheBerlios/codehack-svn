import os

fils = os.listdir('.')

for fil in fils:
    if not fil.endswith('.py'): continue
    c = file(fil, 'r').read()
    if not c.startswith('# Copyright (C) 2004 R. Sridhar'): continue
    c = '# Copyright (C) 2004 Sridhar .R <sridhar@users.berlios.de>\n' + \
        c.split('\n', 1)[1]
    file(fil, 'w').write(c)


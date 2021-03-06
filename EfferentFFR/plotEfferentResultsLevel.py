import pylab as pl
from scipy import io
import numpy as np
# Adding Files and locations
froot = '/home/hari/Documents/PythonCodes/EfferentFFR/LevelControl/'

carr100 = True
noise = True

if carr100:
    xlim = (70, 200)
    if noise:
        froot = froot + 'Noisecarrier100/'
    else:
        froot = froot + 'PTCarr100/'
else:
    xlim = (250, 500)

subj = 'I11'

fpath = froot + subj + '/'

# These are so that the generated files are organized better
respath = fpath + 'RES/'

condstemlist = ['70dBSPL', '64dBSPL', '58dBSPL']

pl.figure()
for k, cond in enumerate(condstemlist):
    fname = respath + subj + '_' + cond + '_results.mat'
    dat = io.loadmat(fname)
    f = dat['f'].squeeze()

    cpow = dat['cpow'].squeeze()
    cplv = dat['cplv'].squeeze()
    Sraw = dat['Sraw'].squeeze()

    # Plot PLV
    ax1 = pl.subplot(3, 1, 1)
    pl.plot(f, 10*np.log10(cpow), linewidth=2)
    pl.hold(True)
    pl.ylabel('Response Magnitude (uV^2)', fontsize=16)
    pl.title(' Subject ' + subj + ' Efferent FFR results')
    pl.legend(condstemlist)

    # Plot power
    ax2 = pl.subplot(3, 1, 2, sharex=ax1)
    pl.plot(f, cplv, linewidth=2)
    pl.hold(True)
    pl.ylabel('Phase locking value', fontsize=16)

    # Plot raw power
    ax3 = pl.subplot(3, 1, 3, sharex=ax1)
    ch = [3, 4, 25, 26, 30, 31]
    pl.plot(f, Sraw[ch, :].mean(axis=0), linewidth=2)
    pl.hold(True)
    pl.ylabel('Raw power', fontsize=16)
    pl.xlabel('Frequency (Hz)', fontsize=16)

pl.xlim(xlim)
pl.show()

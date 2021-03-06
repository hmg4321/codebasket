import mne
import numpy as np
import os
import fnmatch
from anlffr.preproc import find_blinks
from mne.preprocessing.ssp import compute_proj_epochs
from mne.cov import compute_covariance

# Adding Files and locations
# froot = '/home/hari/Documents/PythonCodes/voices/'
froot = '/autofs/cluster/transcend/hari/voices/'

subjlist = ['093302', ]
para = 'speech'
epochs = []
sss = True
for subj in subjlist:

    fpath = froot + subj + '/'
    if sss:
        ssstag = '_sss'
    else:
        ssstag = ''

    fifs = fnmatch.filter(os.listdir(fpath), subj + '_' + para +
                          '_?_raw' + ssstag + '.fif')
    print 'Viola!', len(fifs),  'files found!'
    if len(fifs) > 1:
        print 'Concatenating multiple files..'
    for k, fifname in enumerate(fifs):
        fifs[k] = fpath + fifname
    # Load data and read event channel
    raw = mne.io.Raw(fifs, preload=True)
    eves = mne.find_events(raw, stim_channel='STI101', shortest_event=1)

    # Filter the data for ERPs
    raw.filter(l_freq=0.5, h_freq=144.0, l_trans_bandwidth=0.15,
               picks=np.arange(0, 306, 1))

    # raw.apply_proj()
    fs = raw.info['sfreq']

    # SSP for blinks
    blinks = find_blinks(raw, ch_name='EOG062')
    blinkname = fpath + subj + '_' + para + '_blinks' + ssstag + '-eve.fif'
    mne.write_events(blinkname, blinks)
    epochs_blinks = mne.Epochs(raw, blinks, 998, tmin=-0.25,
                               tmax=0.25, proj=True,
                               baseline=(-0.25, 0),
                               reject=dict(grad=8000e-13,
                                           mag=8e-12))
    blink_projs = compute_proj_epochs(epochs_blinks, n_grad=2,
                                      n_mag=2, n_eeg=0,
                                      verbose='DEBUG')
    raw.add_proj(blink_projs)

    # SSP for cardiac
    ekg_name = 'ECG063' if 'ECG063' in raw.ch_names else 'MEG1421'
    ekg_thresh = 300e-6 if 'ECG063' in raw.ch_names else 1.5e-12
    qrs = find_blinks(raw, ch_name=ekg_name, h_freq=100.0,
                      thresh=ekg_thresh, event_id=999)
    qrsname = fpath + subj + '_' + para + '_qrs' + ssstag + '-eve.fif'
    mne.write_events(qrsname, qrs)
    epochs_qrs = mne.Epochs(raw, qrs, 999, tmin=-0.1,
                            tmax=0.1, proj=True,
                            baseline=(-0.1, 0),
                            reject=dict(grad=8000e-13,
                                        mag=8e-12))
    qrs_projs = compute_proj_epochs(epochs_qrs, n_grad=2,
                                    n_mag=2, n_eeg=0,
                                    verbose='DEBUG')
    raw.add_proj(qrs_projs)
    useProj = True

    evokeds = []
    condlist = [1, 2, 3, 4, 5, 6, 7, 8]
    condnames = ['SpeechA', 'SpeechB', 'JabberA', 'JabberB',
                 'MSSB', 'SWSB', 'NoiseA', 'NoiseB']

    for k, condstem in enumerate(condnames):
        cond = condlist[k]
        print 'Running Subject', subj, 'Condition', condstem

        # Epoching events of type
        epochs = mne.Epochs(raw, eves, cond, tmin=-0.5, proj=useProj,
                            tmax=2.0, baseline=(-0.3, 0.0), name=condstem,
                            reject=dict(grad=5000e-13, mag=5e-12))
        epo_name = (fpath + subj + '_' + para + '_' + condstem +
                    ssstag + '-epo.fif')
        epochs.save(epo_name)
        evokeds += [epochs.average(), ]

    avename = subj + '_' + para + ssstag + '-ave.fif'
    mne.write_evokeds(fpath + avename, evokeds)

    # Compute covariance
    epochs_all = mne.Epochs(raw, eves, condlist, tmin=-0.3, proj=useProj,
                            tmax=0.0, baseline=(-0.3, 0.0), name=condstem,
                            reject=dict(grad=5000e-13, mag=5e-12))
    cov = compute_covariance(epochs_all, tmin=-0.3, tmax=0.0)
    covname = subj + '_' + para + ssstag + '_collapse-cov.fif'
    cov.save(fpath + covname)

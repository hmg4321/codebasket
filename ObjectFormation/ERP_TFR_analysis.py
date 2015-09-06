import mne
import numpy as np
import os
import fnmatch
from anlffr.preproc import find_blinks
from mne.preprocessing.ssp import compute_proj_epochs
from mne.cov import compute_covariance
from mne.time_frequency import tfr_multitaper

# Adding Files and locations
# froot = '/Users/hari/Documents/Data/ObjectFormation/'
froot = '/autofs/cluster/transcend/hari/ObjectFormation/'

subjlist = ['086901', ]
para = 'object'
epochs = []
sss = True
eog = False
ekg = False
for subj in subjlist:

    fpath = froot + subj + '/'

    # These are so that the generated files are organized better
    respath = fpath + 'RES/'
    if sss:
        ssstag = '_sss'
    else:
        ssstag = ''

    fifs = fnmatch.filter(os.listdir(fpath), subj + '_' + para + '_?_raw' +
                          ssstag + '.fif')
    print 'Viola!', len(fifs),  'files found!'
    if len(fifs) > 1:
        print 'Warning! Using multitple raw files!'
    for k, fif in enumerate(fifs):
        fifs[k] = fpath + fif

    # Load data and read event channel
    raw = mne.io.Raw(fifs, preload=True)
    eves = mne.find_events(raw, stim_channel='STI101', shortest_event=1)

    if not sss:
        raw.info['bads'] += ['MEG1013', 'MEG1623', 'MEG2342', 'MEG2513',
                             'MEG2542']
    # Filter the data for ERPs
    raw.filter(l_freq=1.0, h_freq=144, l_trans_bandwidth=0.15,
               picks=np.arange(0, 306, 1))

    # raw.apply_proj()
    fs = raw.info['sfreq']
    removeblinks = True

    if removeblinks:
        # SSP for blinks
        blinks = find_blinks(raw, ch_name=['EOG062', ])
        blinkname = (fpath + subj + '_' + para + '_blinks_erp' + ssstag +
                     '-eve.fif')
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

    # SSP for cardiac artifact
    qrs = find_blinks(raw, ch_name=['MEG1421', ], h_freq=100.0, event_id=999,
                      thresh=1e-12)
    qrsname = fpath + subj + '_' + para + '_qrs_erp' + ssstag + '-eve.fif'
    mne.write_events(qrsname, qrs)
    epochs_qrs = mne.Epochs(raw, qrs, 999, tmin=-0.1,
                            tmax=0.25, proj=True,
                            baseline=(-0.1, 0),
                            reject=dict(grad=8000e-13,
                                        mag=8e-12))
    qrs_projs = compute_proj_epochs(epochs_qrs, n_grad=2,
                                    n_mag=2, n_eeg=0,
                                    verbose='DEBUG')
    raw.add_proj(qrs_projs)

    evokeds = []
    condnames = ['coh07', 'coh14', 'coh20']
    condlists = [3, 2, 1]
    eves2 = np.zeros((eves.shape[0]*2, 3), dtype=np.int)
    fs_int = int(raw.info['sfreq'])
    for k, row in enumerate(eves):
        eves2[2*k, :] = row + np.asarray([fs_int, 0, 0])
        eves2[2*k + 1, :] = row + np.asarray([2*fs_int, 0, 0])

    for k, condstem in enumerate(condnames):
        condlist = condlists[k]
        print 'Running Subject', subj, 'Condition', condstem

        # Epoching events of type
        epochs = mne.Epochs(raw, eves2, condlist, tmin=-0.2, proj=True,
                            tmax=1.5, baseline=(-0.2, 0.0), name=condstem,
                            reject=dict(grad=5000e-13, mag=5e-12))
        evokeds += [epochs.average(), ]
        freqs = np.arange(5., 70., 1.)
        n_cycles = freqs * 0.2
        power, itc = tfr_multitaper(epochs, freqs, n_cycles,
                                    time_bandwidth=2.0, n_jobs=-1)
        fname_pow = subj + ssstag + '_' + para + '_pow_' + condstem + '-tfr.h5'
        fname_itc = subj + ssstag + '_' + para + '_itc_' + condstem + '-tfr.h5'
        power.save(fpath + fname_pow)
        itc.save(fpath + fname_itc)

    # Now save overall onset N100
    epochs = mne.Epochs(raw, eves, condlists, tmin=-0.2, proj=True,
                        tmax=1.5, baseline=(-0.2, 0.0), name=condstem,
                        reject=dict(grad=5000e-13, mag=5e-12))
    evokeds += [epochs.average(), ]
    avename = subj + ssstag + '_' + para + '_collapse-ave.fif'
    mne.write_evokeds(fpath + avename, evokeds)

    # Compute covatiance
    cov = compute_covariance(epochs, tmin=-0.2, tmax=0.0)
    covname = subj + ssstag + '_' + para + '_collapse-cov.fif'
    cov.save(fpath + covname)

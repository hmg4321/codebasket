"""
==================================================
Compute MNE-dSPM inverse solution on single epochs
==================================================

Compute dSPM inverse solution on single trial epochs restricted
to a brain label.

"""
# Author: Hari Bharadwaj <hari@nmr.mgh.harvard.edu>
#
# Compyright 2015. All Rights Reserved.

import numpy as np
import matplotlib.pyplot as plt
import mne
from mne.minimum_norm import apply_inverse_epochs, read_inverse_operator
from mne.minimum_norm import apply_inverse
from anlffr.tfr import tfr_multitaper, rescale, plot_tfr

froot = '/autofs/cluster/transcend/hari/ObjectFormation/'
subj = '093302'
para = 'object'
cond = 'coh20'
sss = True
if sss:
    ssstag = '_sss'
else:
    ssstag = ''

fname_inv = froot + '/' + subj + '/' + subj + '_' + para + ssstag + '-inv.fif'
label_name = 'object_manual-lh'
fname_label = froot + '/' + subj + '/' + subj + '_%s.label' % label_name

# Using the same inverse operator when inspecting single trials Vs. evoked
snr = 3.0  # Standard assumption for average data but using it for single trial
lambda2 = 1.0 / snr ** 2

method = "dSPM"  # use dSPM method (could also be MNE or sLORETA)

# Load operator and labels
inverse_operator = read_inverse_operator(fname_inv)
label = mne.read_label(fname_label)


# Read epochs
fname_epochs = (froot + '/' + subj + '/' + subj + ssstag + '_' + para + '_' +
                cond + '-epo.fif')
epochs = mne.read_epochs(fname_epochs)

# Get evoked data (averaging across trials in sensor space)
evoked = epochs.average()

# Compute inverse solution and stcs for each epoch
# Use the same inverse operator as with evoked data (i.e., set nave)
# If you use a different nave, dSPM just scales by a factor sqrt(nave)
stcs = apply_inverse_epochs(epochs, inverse_operator, lambda2, method, label,
                            nave=evoked.nave)

stc_evoked = apply_inverse(evoked, inverse_operator, lambda2, method)

stc_evoked_label = stc_evoked.in_label(label)

# Mean across trials but not across vertices in label
mean_stc = sum(stcs) / len(stcs)

# compute sign flip to avoid signal cancelation when averaging signed values
flip = mne.label_sign_flip(label, inverse_operator['src'])

label_mean = np.mean(mean_stc.data, axis=0)
label_mean_flip = np.mean(flip[:, np.newaxis] * mean_stc.data, axis=0)

# Get inverse solution by inverting evoked data
stc_evoked = apply_inverse(evoked, inverse_operator, lambda2, method)

# apply_inverse() does whole brain, so sub-select label of interest
stc_evoked_label = stc_evoked.in_label(label)

# Average over label (not caring to align polarities here)
label_mean_evoked = np.mean(stc_evoked_label.data, axis=0)

###############################################################################
# View activation time-series to illustrate the benefit of aligning/flipping

times = 1e3 * stcs[0].times  # times in ms

plt.figure()
h0 = plt.plot(times, mean_stc.data.T, 'k')
h1, = plt.plot(times, label_mean, 'r', linewidth=3)
h2, = plt.plot(times, label_mean_flip, 'g', linewidth=3)
plt.legend((h0[0], h1, h2), ('all dipoles in label', 'mean',
                             'mean with sign flip'))
plt.xlabel('time (ms)')
plt.ylabel('dSPM value')
plt.show()

###############################################################################
# Viewing single trial dSPM and average dSPM for unflipped pooling over label
# Compare to (1) Inverse (dSPM) then average, (2) Evoked then dSPM

# Single trial
plt.figure()
for k, stc_trial in enumerate(stcs):
    plt.plot(times, np.mean(stc_trial.data, axis=0).T, 'k--',
             label='Single Trials' if k == 0 else '_nolegend_',
             alpha=0.5)

# Single trial inverse then average.. making linewidth large to not be masked
plt.plot(times, label_mean, 'b', linewidth=6,
         label='dSPM first, then average')

# Evoked and then inverse
plt.plot(times, label_mean_evoked, 'r', linewidth=2,
         label='Average first, then dSPM')

plt.xlabel('time (ms)')
plt.ylabel('dSPM value')
plt.legend()
plt.show()

###############################################################################
epo_array = np.zeros((len(stcs), 1, stcs[0].shape[1]))
nVerts = stc_evoked_label.shape[0]
corr_list = np.zeros(nVerts)
for k in range(nVerts):
    corr_list[k] = np.corrcoef(label_mean_evoked,
                               stc_evoked_label.data[k, :])[0, 1]
topvert = np.argmax(np.abs(corr_list))
for k, stc in enumerate(stcs):
    epo_array[k, 0, :] = stc.data[topvert, :]

freqs = np.arange(5., 90., 2.)
n_cycles = freqs * 0.2
power, itc, faketimes = tfr_multitaper(epo_array, epochs.info['sfreq'],
                                       freqs, n_cycles=n_cycles,
                                       time_bandwidth=2.0, zero_mean=True)
power_scaled = rescale(power, times, baseline=(-0.2, 0.),
                       mode='zlogratio')
plot_tfr(power_scaled, times, freqs)

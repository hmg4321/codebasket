import mne


# Adding Files and locations
# froot = '/Users/hari/Documents/Data/ObjectFormation/'
froot = '/autofs/cluster/transcend/hari/voices/'
mriroot = '/autofs/cluster/transcend/MRI/WMA/recons/'
subjlist = ['093302', ]
para = 'speech'
sss = True

for subj in subjlist:

    fpath = froot + subj + '/'

    if sss:
        ssstag = '_sss'
    else:
        ssstag = ''

    covname = fpath + subj + '_' + para + ssstag + '_collapse-cov.fif'
    fwdname = fpath + subj + '_' + para + ssstag + '-fwd.fif'
    rawname = fpath + subj + '_' + para + '_1_raw' + ssstag + '.fif'
    trans = fpath + subj + '_' + para + '-trans.fif'
    invname = fpath + subj + '_' + para + ssstag + '-inv.fif'

    # Assume source space setup and bem solution already done
    src = mriroot + subj + '/bem/' + subj + '-ico-5-src.fif'
    bem = mriroot + subj + '/bem/' + subj + '-5120-bem-sol.fif'
    raw = mne.io.Raw(rawname)
    fwd = mne.make_forward_solution(raw.info, trans, src, bem, fname=fwdname,
                                    meg=True, eeg=False, verbose=True)

    # convert to surface orientation for fixed orientation to work
    fwd = mne.convert_forward_solution(fwd, surf_ori=True)
    # Make fixed orientation MEG only inverse
    cov = mne.read_cov(covname)
    inv = mne.minimum_norm.make_inverse_operator(raw.info, fwd, cov,
                                                 fixed=True, verbose=True)
    mne.minimum_norm.write_inverse_operator(invname, inv, verbose=True)

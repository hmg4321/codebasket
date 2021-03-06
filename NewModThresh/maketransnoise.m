function noise = maketransnoise(fc,fm,m,fs,bwnoise,bwenv,dur,rise,playplot)
% USAGE:
%----------------------------------------------------
%  x = maketransnoise(fc,fm,m,fs,bw,dur,rise,playplot);
%----------------------------------------------------
%    fc - Center frequency of the noise band
%    fm - Modulation frequency
%    m - Modulation Depth
%    fs - Sampling frequency
%    bwnoise - Bandwidth of the noise band
%    bwenv - twice the low-pass filter cutoff applied on the envelope (Hz)
%    dur - Duration of the sound
%    rise - Ramp duration (each side)
%    playplot - Whether to play and plot the sound
%----------------------------------------------------

if(~exist('playplot','var'))
    playplot = 0;
end

fmin = fc - bwnoise/2;
fmax = fc + bwnoise/2;


t = (0:(1/fs):(dur - 1/fs))';


%% Making Noise

fstep = 1/dur; %Frequency bin size

hmin = ceil(fmin/fstep);
hmax = floor(fmax/fstep);


phase = rand(hmax-hmin+1,1)*2*pi;

noiseF = zeros(numel(t),1);
noiseF(hmin:hmax) = exp(1j*phase);
noiseF((end-hmax+1):(end-hmin+1)) = exp(-1*1j*phase);

noise = ifft(noiseF,'symmetric');

env = sin(2*pi*fm*t);
env = env.*(env > 0);

% Making a filter whose impulse response if purely positive (to avoid phase
% jumps) so that the filtered envelope is purely positive. Using a dpss
% window to minimize sidebands. For a bandwidth of bw, to get the shortest
% filterlength, we need to restrict time-bandwidth product to a minimum.
% Thus we need a length*bw = 2 => length = 2/bw (second). Hence filter
% coefficients are calculated as follows:
b = dpss(floor(2*fs/bwenv),1,1);  % Using to increase actual bw when rounding
b = b-b(1);
env = filter(b,1,env);
env = env(1:numel(t));
env = env/max(env);

% Imposing depth

if((m < 0) || (m > 1))
    fprintf(2,'WARNING! Making m = 1\n');
    m = 1;
end
env = m*env + (1 - m);


noise = env.*noise;

noise = scaleSound(rampsound(noise,fs,rise));


if(playplot)
    plot(t,noise);
    [pxx,f] = pwelch(noise,[],[],[],fs);
    figure; plot(f,pxx);
    sound(noise,fs);
end


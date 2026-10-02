"""Blocos de sintese dos Reels da MovCode: filtros, reverb, instrumentos,
efeitos, tratamento da voz e master. Tudo sintetizado (nada de samples).

Cada Reels tem o seu synth.py, que importa daqui (from sintese import *),
compoe a trilha nos buses e chama voz() e master().
"""
import json
import os

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from numba import njit
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt

FS = 48000
rng = np.random.default_rng(7)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def nm(s):  # "A3" -> midi
    name, octv = s[:-1], int(s[-1])
    return 12 * (octv + 1) + NOTE[name]


def tt(n):
    return np.arange(n) / FS


# ---------------------------------------------------------------- filtros
def sos(kind, f, order=2):
    if kind == 'bp':
        return butter(order, [f[0] / (FS / 2), f[1] / (FS / 2)], btype='band', output='sos')
    return butter(order, f / (FS / 2), btype=kind, output='sos')


def lp(x, f, o=2):
    return sosfilt(sos('low', f, o), x, axis=0)


def hp(x, f, o=2):
    return sosfilt(sos('high', f, o), x, axis=0)


def bp(x, lo, hi, o=2):
    return sosfilt(sos('bp', (lo, hi), o), x, axis=0)


@njit(cache=True)
def svf(x, fc, q, mode):
    """Filtro de estado variavel com corte por amostra (0=LP, 1=BP, 2=HP)."""
    y = np.zeros_like(x)
    ic1 = 0.0
    ic2 = 0.0
    k = 1.0 / q
    for n in range(x.shape[0]):
        f = fc[n]
        if f > FS * 0.45:
            f = FS * 0.45
        g = np.tan(np.pi * f / FS)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x[n] - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        if mode == 0:
            y[n] = v2
        elif mode == 1:
            y[n] = v1
        else:
            y[n] = x[n] - k * v1 - v2
    return y




# ---------------------------------------------------------------- buses
def bus(dur):
    return np.zeros((int(dur * FS), 2))


def add(b, sig, t0, g=1.0, pan=0.0):
    """Mistura sinal mono (ou estereo) no bus a partir de t0 (s)."""
    N = len(b)
    i0 = int(round(t0 * FS))
    if i0 >= N:
        return
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        st = np.stack([sig * np.cos(a), sig * np.sin(a)], axis=1) * np.sqrt(2)
    else:
        st = sig
    if i0 < 0:
        st = st[-i0:]
        i0 = 0
    n = min(len(st), N - i0)
    b[i0:i0 + n] += st[:n] * g




def env_ad(n, a, d):
    t = tt(n)
    e = np.exp(-t / d)
    if a > 0:
        e *= np.clip(t / a, 0, 1)
    return e


def noise(n):
    return rng.standard_normal(n)


# ---------------------------------------------------------------- reverb
def make_ir(t60=2.2, pre=0.012, damp=6000, seed=3):
    r = np.random.default_rng(seed)
    n = int(t60 * FS)
    t = tt(n)
    decay = np.exp(-6.9 * t / t60)
    ir = np.zeros((n, 2))
    for c in range(2):
        x = r.standard_normal(n) * decay
        x = lp(x, damp)
        # reflexoes iniciais
        for k in range(10):
            d = int((pre + r.uniform(0.003, 0.06)) * FS)
            x[d] += r.uniform(-.8, .8) * (1 - k / 12)
        ir[:, c] = x
    ir /= np.sqrt(np.sum(ir ** 2) / 2)
    return ir


def reverb(x, ir, wet):
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - wet) + y * wet


IR_BIG = make_ir(3.2, damp=5000)
IR_ROOM = make_ir(0.9, damp=7000, seed=5)
IR_PLATE = make_ir(1.8, damp=8000, seed=9)

# ---------------------------------------------------------------- instrumentos
_noise_bank = noise(FS * 4)


def kick(g=1.0, f0=48, punch=120, dec=0.3, click=0.6):
    n = int(0.7 * FS)
    t = tt(n)
    f = f0 + punch * np.exp(-t / 0.028) + 30 * np.exp(-t / 0.004)
    ph = 2 * np.pi * np.cumsum(f) / FS
    s = np.sin(ph) * np.exp(-t / dec) * np.clip(t / 0.0015, 0, 1)
    c = hp(_noise_bank[:n], 2000) * np.exp(-t / 0.004) * click
    return np.tanh(1.6 * (s + c)) * g


def heartbeat():
    a = kick(0.9, f0=38, punch=55, dec=0.22, click=0.05)
    b = kick(0.55, f0=36, punch=45, dec=0.18, click=0.03)
    out = np.zeros(int(0.9 * FS))
    out[:len(a)] += lp(a, 180)
    d = int(0.17 * FS)
    out[d:d + len(b)] += lp(b, 160)[:len(out) - d]
    return out


def clap(g=1.0):
    n = int(0.5 * FS)
    t = tt(n)
    e = np.zeros(n)
    for k, off in enumerate([0, 0.009, 0.019, 0.028]):
        i = int(off * FS)
        e[i:] += np.exp(-(t[:n - i]) / (0.008 if k < 3 else 0.13)) * (0.8 if k < 3 else 1)
    s = bp(noise(n), 900, 2600) * e
    return s * g * 1.4


def snare(g=1.0, dec=0.14):
    n = int(0.4 * FS)
    t = tt(n)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.6
    nz = bp(noise(n), 1500, 7000) * np.exp(-t / dec)
    return np.tanh((tone + nz) * 1.3) * g


def rim(g=1.0):
    n = int(0.12 * FS)
    t = tt(n)
    s = (np.sin(2 * np.pi * 820 * t) + .6 * np.sin(2 * np.pi * 1650 * t)) * np.exp(-t / 0.025)
    s += hp(noise(n), 3000) * np.exp(-t / 0.004) * .5
    return s * g


def hat(g=1.0, dec=0.035):
    n = int(min(0.6, dec * 8) * FS)
    t = tt(n)
    s = hp(noise(n), 7500, 4) * np.exp(-t / dec)
    return s * g


def crash(g=1.0, dec=1.6):
    n = int(dec * 3 * FS)
    t = tt(n)
    s = hp(noise(n), 4500, 2) * np.exp(-t / dec)
    s += hp(np.sin(2 * np.pi * 5200 * t + 3 * np.sin(2 * np.pi * 7300 * t)), 3000) * np.exp(-t / (dec * .6)) * .15
    return s * g


def tom(f=110, g=1.0):
    n = int(0.5 * FS)
    t = tt(n)
    fr = f * (1 + .5 * np.exp(-t / 0.04))
    s = np.sin(2 * np.pi * np.cumsum(fr) / FS) * np.exp(-t / 0.18)
    s += bp(noise(n), 200, 2000) * np.exp(-t / 0.03) * .3
    return s * g


def saw(f, n, phase=0.0):
    p = (phase + np.cumsum(np.full(n, f) if np.isscalar(f) else f) / FS) % 1.0
    return 2 * p - 1


def supersaw(m, n, voices=7, detune=0.18, seed=0):
    r = np.random.default_rng(seed + m)
    f = midi(m)
    out = np.zeros((n, 2))
    for v in range(voices):
        d = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune
        fv = f * 2 ** (d / 12)
        s = saw(fv, n, r.random())
        pan = (v / (voices - 1)) * 2 - 1
        a = (pan * .8 + 1) * np.pi / 4
        out[:, 0] += s * np.cos(a)
        out[:, 1] += s * np.sin(a)
    return out / voices


def chord_stab(notes, dur, g=1.0, cutoff=3800, att=0.004, dec=None):
    n = int((dur + 0.05) * FS)
    out = np.zeros((n, 2))
    for i, m in enumerate(notes):
        out += supersaw(m, n, seed=i * 13)
    t = tt(n)
    e = np.clip(t / att, 0, 1) * (np.exp(-t / dec) if dec else 1) * np.clip((dur + .05 - t) / .05, 0, 1)
    fc = cutoff * (0.45 + 0.55 * np.exp(-t / 0.18))
    for c in range(2):
        out[:, c] = svf(out[:, c] * e, fc, 0.9, 0)
    return out * g / len(notes) * 2.2


def pad(notes, dur, g=1.0, cutoff=1400, att=0.6, rel=0.8, seed=0):
    n = int((dur + rel) * FS)
    out = np.zeros((n, 2))
    for i, m in enumerate(notes):
        out += supersaw(m, n, voices=5, detune=0.12, seed=seed + i * 7)
    t = tt(n)
    e = np.clip(t / att, 0, 1) * np.clip((dur + rel - t) / rel, 0, 1)
    fc = np.full(n, float(cutoff)) * (1 + .15 * np.sin(2 * np.pi * 0.3 * t))
    for c in range(2):
        out[:, c] = svf(out[:, c] * e, fc, 0.7, 0)
    return out * g / len(notes) * 2


def pluck(m, g=1.0, dec=0.22, bright=5200):
    n = int(0.6 * FS)
    t = tt(n)
    f = midi(m)
    s = 0.6 * saw(f, n) + 0.4 * np.sign(np.sin(2 * np.pi * f * t))
    fc = 300 + bright * np.exp(-t / 0.06)
    s = svf(s * np.exp(-t / dec), fc, 1.2, 0)
    return s * g


def sub(m, dur, g=1.0):
    n = int((dur + .03) * FS)
    t = tt(n)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
    e = np.clip(t / 0.008, 0, 1) * np.clip((dur + .03 - t) / 0.03, 0, 1)
    return np.tanh(1.3 * s * e) * g


def bell(f, g=1.0, dec=0.35):
    n = int(dec * 5 * FS)
    t = tt(n)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
    s += 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / (dec * .4))
    s += 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / (dec * .2))
    s *= np.clip(t / 0.002, 0, 1)
    return s * g


def ding(f1=1318.5, f2=1760, g=1.0):
    a = bell(f1, 1, .22)
    b = bell(f2, 1, .3)
    out = np.zeros(len(b) + int(.08 * FS))
    out[:len(a)] += a
    out[int(.08 * FS):int(.08 * FS) + len(b)] += b
    return out * g * .5


def pop(g=1.0, f0=900, f1=280, d=0.05):
    n = int(0.15 * FS)
    t = tt(n)
    f = f1 + (f0 - f1) * np.exp(-t / d * 2.5)
    s = np.sin(2 * np.pi * np.cumsum(f) / FS) * np.exp(-t / d) * np.clip(t / 0.001, 0, 1)
    return s * g


def bloop(g=1.0, f0=380, f1=980):
    n = int(0.22 * FS)
    t = tt(n)
    f = f0 + (f1 - f0) * (1 - np.exp(-t / 0.03))
    s = np.sin(2 * np.pi * np.cumsum(f) / FS) * np.exp(-t / 0.07) * np.clip(t / 0.003, 0, 1)
    return s * g


def blip(m, g=1.0, dec=0.09):
    n = int(0.3 * FS)
    t = tt(n)
    f = midi(m)
    s = (np.sin(2 * np.pi * f * t) + 0.3 * np.sign(np.sin(2 * np.pi * f * t))) * np.exp(-t / dec) * np.clip(t / 0.002, 0, 1)
    return lp(s, 6000) * g


def click(g=1.0):
    n = int(0.02 * FS)
    t = tt(n)
    return bp(noise(n), 2000, 6000) * np.exp(-t / 0.003) * g


def whoosh(dur=0.5, g=1.0, f_lo=300, f_hi=3500, rev=False, pan_sweep=True):
    n = int(dur * FS)
    t = tt(n) / dur
    shape = np.sin(np.pi * t) ** 2 if not rev else t ** 3
    fc = f_lo * (f_hi / f_lo) ** (np.sin(np.pi * t) if not rev else t)
    x = noise(n)
    s = svf(x, fc, 1.6, 1) * shape
    s = s / (np.max(np.abs(s)) + 1e-9)
    if pan_sweep:
        p = (t * 2 - 1) * .8
        a = (p + 1) * np.pi / 4
        return np.stack([s * np.cos(a), s * np.sin(a)], 1) * g * np.sqrt(2)
    return s * g


def impact(g=1.0, f0=58, sub_dec=1.1, bright=1.0):
    n = int(3.0 * FS)
    t = tt(n)
    f = 30 + (f0 - 30) * np.exp(-t / 0.6) + 80 * np.exp(-t / 0.02)
    s = np.sin(2 * np.pi * np.cumsum(f) / FS) * np.exp(-t / sub_dec)
    nz = lp(noise(n), 2500) * np.exp(-t / 0.18) * 0.7 * bright
    nz += hp(noise(n), 3000) * np.exp(-t / 0.05) * 0.3 * bright
    return np.tanh(1.4 * (s + nz)) * g


def riser(dur, g=1.0, f_lo=250, f_hi=9000, pitch=(nm('A2'), nm('A5'))):
    n = int(dur * FS)
    t = tt(n) / dur
    fc = f_lo * (f_hi / f_lo) ** (t ** 1.6)
    s = svf(noise(n), fc, 2.0, 1) * (t ** 2.2)
    s /= np.max(np.abs(s)) + 1e-9
    fp = midi(pitch[0]) * (midi(pitch[1]) / midi(pitch[0])) ** (t ** 1.3)
    tone = saw(fp, n) * 0.35 + saw(fp * 1.006, n) * 0.35
    tone = svf(tone, 400 + 6000 * t ** 2, 1.0, 0) * (t ** 2.5)
    return (s * .8 + tone * .5) * g


def scratch(dur, g=1.0):
    n = int(dur * FS)
    t = tt(n)
    am = np.abs(np.sin(2 * np.pi * (7 + 4 * np.sin(2 * np.pi * 1.3 * t)) * t)) ** 2
    s = bp(noise(n), 2500, 7500) * am * np.clip(t / .01, 0, 1) * np.clip((dur - t) / .02, 0, 1)
    return s * g


def glitch(dur, g=1.0, seed=1):
    r = np.random.default_rng(seed)
    n = int(dur * FS)
    out = np.zeros(n)
    i = 0
    while i < n:
        L = int(r.choice([0.018, 0.037, 0.075]) * FS)
        L = min(L, n - i)
        k = r.random()
        t = tt(L)
        if k < .4:
            seg = np.sign(np.sin(2 * np.pi * r.uniform(200, 2400) * t))
        elif k < .7:
            seg = np.round(noise(L) * 3) / 3
        else:
            seg = np.zeros(L)
        out[i:i + L] = seg * (0.4 + .6 * r.random())
        i += L
    return lp(out, 7000) * g


def compress(x, thr_db=-20, ratio=3.5, att=0.004, rel=0.12, makeup_db=6):
    env = np.abs(x)
    a = np.exp(-1 / (att * FS))
    r = np.exp(-1 / (rel * FS))
    e = _follow(env, a, r)
    lvl = 20 * np.log10(e + 1e-9)
    over = np.maximum(lvl - thr_db, 0)
    gr = -over * (1 - 1 / ratio)
    return x * 10 ** ((gr + makeup_db) / 20)


@njit(cache=True)
def _follow(x, a, r):
    y = np.zeros_like(x)
    e = 0.0
    for i in range(x.shape[0]):
        v = x[i]
        if v > e:
            e = a * e + (1 - a) * v
        else:
            e = r * e + (1 - r) * v
        y[i] = e
    return y


def limiter(x, ceil=0.89, look=0.003, rel=0.08):
    """Limitador simples com lookahead."""
    peak = np.max(np.abs(x), axis=1)
    L = int(look * FS)
    # maximo deslizante adiantado
    pk = maximum_filter1d(peak, size=2 * L + 1)
    g = np.minimum(1, ceil / (pk + 1e-9))
    # suaviza o retorno
    gs = _follow(1 - g, np.exp(-1 / (0.0008 * FS)), np.exp(-1 / (rel * FS)))
    return x * (1 - gs)[:, None]


# ---------------------------------------------------------------- voz
def voz(vo_cues, pasta, dur, eco=()):
    """Falas audio/L*.wav nos tempos de cues.json: EQ, compressao, eco nas falas
    de `eco` e sala. Devolve (bus estereo da voz, voz mono crua para o ducking)."""
    N = int(dur * FS)
    vo = bus(dur)
    vo_send = bus(dur)
    vo_echo = bus(dur)
    voice_mono = np.zeros(N)
    for key, t0 in vo_cues.items():
        a, sr = sf.read(os.path.join(pasta, f'{key}.wav'))
        a = resample_poly(a, FS, sr)
        a = hp(a, 75)
        i0 = int(t0 * FS)
        voice_mono[i0:i0 + len(a)] += a[:N - i0]
        if key in eco:
            add(vo_echo, a, t0)

    # EQ da voz: corta embolado, presenca, ar
    v = voice_mono
    v = v - 0.25 * bp(v, 250, 450)            # -2,5 dB no embolado
    v = v + 0.35 * bp(v, 2500, 5000)          # presenca
    v = v + 0.2 * hp(v, 9000)                 # ar
    v = v + 0.25 * bp(v, 110, 200)            # corpo
    v = v / (np.max(np.abs(v)) + 1e-9) * 0.7
    v = compress(v, -18, 3.0, makeup_db=4)
    add(vo, v, 0)
    add(vo_send, v * .22, 0)
    # eco dramatico
    echo = vo_echo[:, 0] / (np.max(np.abs(voice_mono)) + 1e-9) * .7
    ech = np.zeros(N)
    for k, d in enumerate([0.3, 0.6, 0.9]):
        i = int(d * FS)
        ech[i:] += echo[:N - i] * (0.32 * .55 ** k)
    ech = lp(hp(ech, 300), 4000)
    vo += np.stack([ech, np.roll(ech, 700)], 1) * .8
    vo = vo + reverb(vo_send, IR_ROOM, 1.0)
    return vo, voice_mono


# ---------------------------------------------------------------- master
def master(music, drums, sfx, send_big, send_plate, vo, voice_mono, kick_times, fim, out, fade=0.5, G_M=0.16, G_S=0.33):
    """Sidechain pelo bumbo, ducking pela voz, reverbs, EQ, fade final, -14 LUFS e
    limitador. Grava mix.wav e os stems (music, sfx, vo) em `out`, com `fim` segundos."""
    N = len(music)
    # sidechain da trilha pelo bumbo
    kick_times = sorted(set(round(k, 4) for k in kick_times))
    sc = np.ones(N)
    for kt in kick_times:
        i0 = int(kt * FS)
        L = int(0.4 * FS)
        seg = 1 - 0.55 * np.exp(-tt(L) / 0.11)
        sc[i0:i0 + L] = np.minimum(sc[i0:i0 + L], seg[:N - i0] if i0 + L > N else seg)
    music *= sc[:, None]

    # ducking pela voz
    venv = _follow(np.abs(voice_mono) / (np.max(np.abs(voice_mono)) + 1e-9), np.exp(-1 / (0.01 * FS)), np.exp(-1 / (0.25 * FS)))
    duck = 10 ** (-10 * np.clip(venv * 6, 0, 1) / 20)
    duck_sfx = 10 ** (-4 * np.clip(venv * 6, 0, 1) / 20)

    wet_big = reverb(send_big, IR_BIG, 1.0)
    wet_plate = reverb(send_plate + drums * 0.05, IR_PLATE, 1.0)
    music_bus = (music + wet_plate * .5) * duck[:, None]
    drum_bus = drums * (0.6 + 0.4 * duck[:, None])
    sfx_bus = (sfx + wet_big * .7) * duck_sfx[:, None]
    music_bus += reverb(music * .12, IR_PLATE, 1.0)
    # EQ do barramento da trilha: tira o embolado e abre o brilho (a voz mora em 300 Hz-4 kHz)
    music_bus = music_bus - 0.4 * bp(music_bus, 170, 480) - 0.15 * bp(music_bus, 900, 2600) + 0.3 * hp(music_bus, 4500)

    music_bus *= G_M
    drum_bus *= G_M
    sfx_bus *= G_S
    mix = music_bus * 0.85 + drum_bus * 0.9 + sfx_bus * 0.75 + vo * 1.15

    # fade final acompanhando o video
    fd = np.ones(N)
    f0, f1 = int((fim - fade) * FS), int(fim * FS)
    fd[f0:f1] = np.linspace(1, 0, f1 - f0) ** 1.5
    fd[f1:] = 0
    for b in (mix, music_bus, drum_bus, sfx_bus, vo):
        b *= fd[:, None]

    meter = pyln.Meter(FS)
    L = int(fim * FS)
    lufs = meter.integrated_loudness(mix[:L])
    gain = 10 ** ((-14.0 - lufs) / 20)
    print('lufs antes', round(lufs, 2), 'ganho dB', round(20 * np.log10(gain), 2))
    mix *= gain
    mix = limiter(mix, ceil=0.84)
    print('lufs depois', round(meter.integrated_loudness(mix[:L]), 2))
    for b in (music_bus, drum_bus, sfx_bus, vo):
        b *= gain

    os.makedirs(out, exist_ok=True)
    sf.write(os.path.join(out, 'mix.wav'), mix[:L], FS, subtype='PCM_24')
    sf.write(os.path.join(out, 'music.wav'), (music_bus * .85 + drum_bus * .9)[:L], FS, subtype='PCM_24')
    sf.write(os.path.join(out, 'sfx.wav'), (sfx_bus * .75)[:L], FS, subtype='PCM_24')
    sf.write(os.path.join(out, 'vo.wav'), (vo * 1.15)[:L], FS, subtype='PCM_24')
    print('peak', np.max(np.abs(mix)), 'rms', np.sqrt(np.mean(mix ** 2)))
    return mix

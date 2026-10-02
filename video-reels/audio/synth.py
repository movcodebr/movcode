"""Trilha, efeitos e mixagem do Reels da MovCode.

Tudo sintetizado (os instrumentos ficam em sintese.py): 100 BPM, la menor / do maior.
Gera stems (music.wav, sfx.wav, vo.wav) e mix.wav, em 48 kHz estereo.
"""
import json
import os

import numpy as np

from sintese import *  # noqa: F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 38.0
BEAT = 0.6

cues = json.load(open(os.path.join(HERE, '..', 'cues.json')))

# ---------------------------------------------------------------- composicao
music = bus(DUR)   # trilha
drums = bus(DUR)   # bateria (com sidechain proprio)
sfx = bus(DUR)     # efeitos
send_big = bus(DUR)  # reverb grande
send_plate = bus(DUR)

A_MIN = [nm('A3'), nm('C4'), nm('E4'), nm('A4')]
F_MAJ = [nm('F3'), nm('A3'), nm('C4'), nm('F4')]
C_MAJ = [nm('G3'), nm('C4'), nm('E4'), nm('G4')]
G_MAJ = [nm('G3'), nm('B3'), nm('D4'), nm('G4')]
ROOT = {'Am': nm('A1'), 'F': nm('F1'), 'C': nm('C2'), 'G': nm('G1')}
CH = {'Am': A_MIN, 'F': F_MAJ, 'C': C_MAJ, 'G': G_MAJ}
ARP = {'Am': ['A4', 'C5', 'E5', 'A5', 'E5', 'C5', 'E5', 'G5'], 'F': ['F4', 'A4', 'C5', 'F5', 'C5', 'A4', 'C5', 'E5'],
       'C': ['G4', 'C5', 'E5', 'G5', 'E5', 'C5', 'E5', 'D5'], 'G': ['G4', 'B4', 'D5', 'G5', 'D5', 'B4', 'D5', 'F#5']}

kick_times = []

# --- abertura: drone + batimento -------------------------------------------
n = int(8.45 * FS)
t = tt(n)
drone = np.sin(2 * np.pi * 55 * t) * .5 + np.sin(2 * np.pi * 82.41 * t) * .22
drone += svf(saw(55.0, n) * .3, np.full(n, 160.0) + 120 * (t / 8.4) ** 2, 0.8, 0)
drone *= np.clip(t / 1.5, 0, 1) * (0.55 + 0.45 * (t / 8.4))
add(music, drone * .55, 0)
# ar / textura
air = svf(noise(n), 900 + 3000 * (t / 8.4) ** 2, 1.2, 1) * np.clip(t / 2, 0, 1) * (0.2 + .8 * (t / 8.4) ** 2)
add(music, np.stack([air, np.roll(air, 900)], 1) * .05, 0)
for b in [0.0, 0.6, 1.2, 1.8]:
    add(music, heartbeat(), b, .95)
# tensao (cordas sinteticas) a partir de 2.4
n = int(6.1 * FS)
t = tt(n)
strings = np.zeros(n)
for m in [nm('A4'), nm('C5'), nm('E5'), nm('B4')]:
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + m)
    strings += saw(midi(m) * vib, n)
strings = lp(strings, 2600) * (t / 6.0) ** 1.8 * .08
add(music, np.stack([strings, np.roll(strings, 400)], 1), 2.3)
# pulso de baixo em colcheias + relogio
for i in range(int((8.4 - 2.4) / 0.3)):
    tb = 2.4 + i * 0.3
    k = (tb - 2.4) / 6.0
    add(music, lp(sub(nm('A1'), 0.22, .5), 300 + 700 * k), tb, .7)
    add(sfx, click(0.35 if i % 2 == 0 else 0.22), tb, 1, pan=-.3 if i % 2 == 0 else .3)
    if i % 2 == 0:
        add(music, heartbeat(), tb, .55 + .4 * k)
# glitch final da sobrecarga
add(sfx, glitch(0.75, .22, seed=4), 7.55, 1, pan=.2)

# --- S3: silencio dramatico --------------------------------------------------
n = int(2.6 * FS)
t = tt(n)
eerie = (np.sin(2 * np.pi * midi(nm('E5')) * t) * (0.6 + .4 * np.sin(2 * np.pi * 4 * t)) + .4 * np.sin(2 * np.pi * midi(nm('B5')) * t)) * np.clip(t / .8, 0, 1) * np.clip((2.6 - t) / .5, 0, 1)
add(music, eerie * .04, 8.4)
add(send_big, eerie * .06, 8.4)
add(music, np.sin(2 * np.pi * 55 * t) * np.clip(t / .3, 0, 1) * np.clip((2.6 - t) / .6, 0, 1) * .25, 8.4)
for b in [9.0, 9.6, 10.2]:
    add(music, heartbeat(), b, .55)

# --- S4: construcao ----------------------------------------------------------
add(music, pad(A_MIN, 2.3, g=.18, cutoff=600, att=1.2, rel=.2), 10.8)
# virada de caixa acelerando
rolls = []
tb = 11.4
while tb < 13.08:
    k = (tb - 11.4) / 1.68
    step = 0.3 if k < .35 else (0.15 if k < .65 else (0.075 if k < .88 else 0.0375))
    rolls.append((tb, .25 + .6 * k))
    tb += step
for tb, g in rolls:
    add(drums, snare(g * .55, dec=.09), tb, pan=0)
for tb in [12.0, 12.6]:
    add(drums, kick(.8), tb)
    kick_times.append(tb)
add(music, riser(1.75, .32), 11.35)

# --- grooves -----------------------------------------------------------------
def groove(t0, bars, chords, level=1.0, claps=True, stabs=True, arps=True, hats=True, kick_on=True, perc=True, bass=True):
    """chords: lista por meia barra ou por barra (str)."""
    for b in range(bars):
        tb = t0 + b * 2.4
        ch = chords[b] if isinstance(chords[b], (list, tuple)) else [chords[b], chords[b]]
        for half in range(2):
            name = ch[half]
            th = tb + half * 1.2
            if bass:
                add(music, sub(ROOT[name], 1.15, .62 * level), th)
            if stabs:
                for s16 in [0, 3, 6]:
                    add(music, chord_stab(CH[name], 0.12 if s16 else 0.22, g=.30 * level, cutoff=4200), th + s16 * 0.15)
            if arps:
                for i in range(8):
                    m = nm(ARP[name][i])
                    add(music, pluck(m, .11 * level), th + i * 0.15, pan=(-.35 if i % 2 else .35))
        for s in range(16):
            ts = tb + s * 0.15
            if kick_on and s % 4 == 0:
                add(drums, kick(.95 * level), ts)
                kick_times.append(ts)
            if claps and s in (4, 12):
                add(drums, clap(.5 * level), ts)
                add(send_plate, clap(.25 * level), ts)
            if perc and s in (3, 6, 11, 14):
                add(drums, rim(.18 * level), ts, pan=.25)
            if hats:
                if s % 4 == 2:
                    add(drums, hat(.22 * level, .16), ts, pan=-.2)
                elif s % 2 == 1:
                    add(drums, hat(.09 * level, .025), ts, pan=.3)
        # pad de fundo
        add(music, pad(CH[ch[0]], 1.15, g=.09 * level, cutoff=1800, att=.2, rel=.3, seed=b), tb)
        add(music, pad(CH[ch[1]], 1.15, g=.09 * level, cutoff=1800, att=.2, rel=.3, seed=b + 50), tb + 1.2)


# DROP 13.2 – 22.8
groove(13.2, 4, ['Am', 'F', 'C', 'G'])
add(drums, crash(.35), 13.2)
add(send_big, crash(.15), 13.2)
# 22.8 – 24.0 paineis: virada
for s in range(8):
    ts = 22.8 + s * 0.15
    add(drums, snare(.18 + .07 * s, dec=.08), ts)
    if s % 4 == 0:
        add(drums, kick(.9), ts)
        kick_times.append(ts)
for s, f in zip([4, 5, 6, 7], [180, 150, 120, 95]):
    add(drums, tom(f, .5), 22.8 + s * 0.15)
add(music, sub(ROOT['Am'], 1.15, .55), 22.8)
add(music, chord_stab(A_MIN, .22, g=.3), 22.8)
add(drums, crash(.2), 22.8)
# 24.0 – 25.2 respiro
add(music, pad(F_MAJ, 1.2, g=.16, cutoff=900, att=.1, rel=.2), 24.0)
add(music, sub(ROOT['F'], 1.15, .4), 24.0)
add(music, riser(1.2, .2, pitch=(nm('A3'), nm('A5'))), 24.0)
# 25.2 – 28.8 groove de novo
groove(25.2, 1, ['Am'])
groove(27.6, 1, [['F', 'G']], claps=True)
add(drums, crash(.35), 25.2)
add(send_big, crash(.15), 25.2)
# 28.8 – 30.0: construcao para a marca (sobrepoe meia barra G com virada)
for s in range(8):
    ts = 28.8 + s * 0.15
    add(drums, snare(.15 + .06 * s, dec=.07), ts)
    add(drums, snare(.1 + .05 * s, dec=.06), ts + 0.075)
add(music, riser(1.1, .3, pitch=(nm('G3'), nm('G5'))), 28.75)

# OUTRO 30.0 – 37.2
def outro():
    plan = [('C', 30.0, 2.4), ('Am', 32.4, 2.4), ('F', 34.8, 0.6), ('G', 35.4, 0.6)]
    for name, t0, d in plan:
        add(music, pad(CH[name], d, g=.17, cutoff=2200, att=.05, rel=.4, seed=int(t0)), t0)
        add(music, sub(ROOT[name], d - .03, .5), t0)
        steps = int(d / 0.15)
        for i in range(steps):
            add(music, pluck(nm(ARP[name][i % 8]), .085, dec=.3), t0 + i * .15, pan=(-.4 if i % 2 else .4))
    for b in range(int((36.0 - 30.0) / 0.6)):
        tb = 30.0 + b * 0.6
        add(drums, kick(.75), tb)
        kick_times.append(tb)
        add(drums, hat(.16, .14), tb + .3, pan=-.2)
        if b % 2 == 1:
            add(drums, clap(.3), tb)
    add(music, chord_stab(C_MAJ + [nm('C5')], .9, g=.42, cutoff=5000, dec=.5), 30.0)
    # final: acorde de do no pulinho
    add(music, chord_stab(C_MAJ + [nm('C5')], 1.2, g=.4, cutoff=5200, dec=.6), 36.0)
    add(music, sub(ROOT['C'], 1.1, .55), 36.0)
    add(drums, kick(1.0), 36.0)
    kick_times.append(36.0)
    add(drums, crash(.3, 2.0), 36.0)
    add(send_big, chord_stab(C_MAJ, 1.2, g=.25, cutoff=4000, dec=.6), 36.0)


outro()

# ---------------------------------------------------------------- efeitos
# impactos
for ti, g in [(8.4, .8), (13.2, .6), (25.22, .55), (30.0, .7)]:
    add(sfx, impact(g * .75), ti)
    add(send_big, impact(g * .35, bright=1.2), ti)
add(sfx, impact(.35, f0=70, sub_dec=.4), 6.62)
add(sfx, impact(.25, f0=90, sub_dec=.3, bright=1.3), 22.8)
# whooshes
for tc, d, g in [(2.22, .45, .5), (10.62, .4, .3), (12.95, .5, .55), (15.42, .35, .45), (17.8, .4, .45), (20.3, .35, .5), (23.86, .3, .45), (26.22, .35, .4), (29.7, .45, .6), (30.3, .5, .25)]:
    add(sfx, whoosh(d, g), tc - d / 2)
add(sfx, whoosh(.32, .7, 200, 5000, rev=True, pan_sweep=False), 8.08)  # implosao (succao)
add(sfx, riser(.5, .25, f_lo=400, f_hi=8000, pitch=(nm('A4'), nm('A6'))), 1.92)  # zoom no ponto
add(sfx, bloop(.35, 900, 260), 2.83)  # contador assenta

# caos: caderno, planilhas, bolhas
add(sfx, whoosh(.3, .25, 500, 2500), 2.4)
for i in range(5):
    add(sfx, scratch(.24, .12), 2.62 + i * .17, pan=-.2)
add(sfx, scratch(.3, .18), 3.45)
add(sfx, scratch(.33, .14), 3.7, pan=.2)
for ti, (a, b) in [(3.25, (1318.5, 1760)), (5.45, (1174.7, 1568)), (7.02, (1396.9, 1864.7))]:
    add(sfx, ding(a, b, .32), ti, pan=-.15)
for i, ti in enumerate([4.2, 4.6, 5.02]):
    add(sfx, pop(.35, 700 + 120 * i, 250), ti, pan=(-.3 + .3 * i))
add(sfx, pop(.3, 500, 180, .07), 6.0)
add(sfx, pop(.25, 900, 300), 6.1)
penta = [nm(x) for x in ['E6', 'G6', 'A6', 'C7', 'D7', 'E7', 'D6', 'A5']]
r2 = np.random.default_rng(11)
sw = [7.05 + 1.25 * (i / 16) ** .75 for i in range(16)]
for i, ti in enumerate(sw):
    f1 = midi(penta[i % len(penta)])
    add(sfx, ding(f1, f1 * 1.335, .2 + .1 * (i / 16)), ti, pan=r2.uniform(-.8, .8))

# S4
for i in range(10):
    add(sfx, click(.25), 10.74 + i * .024 + (i % 3) * .004, pan=.3)
add(sfx, bloop(.5), 10.99, pan=.25)

# Sites
for i in range(5):
    add(sfx, pop(.16, 1200 + 100 * i, 500, .03), 13.45 + i * .08, pan=.1)
pin = np.zeros(int(.5 * FS))
pd = pop(1, 1600, 400, .08)
pin[:len(pd)] += pd
for k, d in enumerate([.14, .23, .29]):
    c = pop(.5 / (k + 1), 900, 400, .02)
    i = int(d * FS)
    pin[i:i + len(c)] += c
add(sfx, pin * .4, 14.55)
add(sfx, bell(880, .18, .5), 14.72)
add(sfx, bell(1320, .1, .5), 14.9)
add(sfx, bloop(.28, 500, 1200), 14.85, pan=.4)
add(sfx, ding(1568, 2093, .22), 15.05, pan=-.4)

# Lojas
for i in range(3):
    add(sfx, whoosh(.25, .2, 600, 3000), 15.6 + i * .1)
for i, ti in enumerate([16.2, 16.45, 16.7]):
    add(sfx, blip(nm('E6') + [0, 3, 7][i], .22), ti, pan=-.2 + .2 * i)
    add(sfx, pop(.3, 700, 300, .03), ti + .32, pan=-.4)
kach = bell(2093, 1, .4) + np.pad(bell(2637, 1, .5), (0, 0))[:len(bell(2093, 1, .4))]
add(sfx, kach * .3, 16.95)
add(sfx, bell(3136, .12, .6), 17.02)
add(sfx, bell(1046.5, .15, .7), 17.35, pan=.4)

# Sistemas
for i in range(5):
    add(sfx, click(.2), 18.42 + i * .07, pan=-.2)
for i, ti in enumerate([18.95, 19.09, 19.23, 19.37]):
    add(sfx, bell(midi(nm('C6') + [0, 4, 7, 12][i]), .2, .25), ti, pan=.3)
for i in range(12):
    add(sfx, blip(nm('C5') + i * 2, .06, .05), 19.15 + i * .035)

# Automacoes
add(sfx, pop(.4, 500, 150, .08), 20.5)
for i in range(4):
    add(sfx, pop(.2, 1000 + 150 * i, 400, .04), 20.62 + i * .07, pan=[-.5, .5, -.5, .5][i])
PT0 = 20.95
for i in range(4):
    ph0 = (i * .23 + .5) % 1
    first = PT0 + .35 + ((1 - ph0) % 1) / 1.5
    tcur = first
    while tcur < 22.75:
        add(sfx, blip(nm('A6') + [0, 3, 5, 7][i], .07, .05), tcur, pan=[-.5, .5, -.5, .5][i])
        tcur += 1 / 1.5

# Paineis: contador
for i in range(14):
    k = i / 14
    add(sfx, click(.15), 22.85 + .75 * k ** 1.6)
add(sfx, riser(.8, .18, f_lo=600, f_hi=9000, pitch=(nm('A4'), nm('A6'))), 22.85)

# Mercadinho -> industria
add(sfx, pop(.35, 600, 200, .06), 24.0)
add(sfx, whoosh(.38, .3, 150, 1200), 24.65)
add(sfx, whoosh(.38, .3, 150, 1400), 24.9)
rumble = lp(noise(int(1.2 * FS)), 160) * np.exp(-tt(int(1.2 * FS)) / .5) * 2.5
add(sfx, rumble * .3, 25.22)
for i in range(20):
    add(sfx, blip(nm('E7') - (i % 5), .025, .03), 25.45 + i * .022, pan=np.sin(i))

# tamanho / oooo
for i in range(7):
    add(sfx, blip(nm('A4') + [0, 2, 3, 5, 7, 8, 10][i], .12, .07), 27.38 + i * .055, pan=-.3 + .1 * i)
OT = [28.86 + i * .118 for i in range(8)]
for i, ti in enumerate(OT):
    add(sfx, blip(nm('A5') + [0, 2, 3, 5, 7, 8, 10, 12][i], .16 + .02 * i, .08), ti, pan=.1 * i - .3)
    add(sfx, pop(.15, 300 + 60 * i, 120, .05), ti)

# marca
r3 = np.random.default_rng(5)
for i in range(26):
    add(sfx, bell(r3.uniform(2500, 6000), .03, .25), 30.0 + r3.uniform(0, .9) ** 1.5, pan=r3.uniform(-.9, .9))
add(sfx, whoosh(.45, .2, 800, 5000), 30.22)
add(sfx, bloop(.35, 420, 900), 31.7)
add(sfx, pop(.25, 1000, 400), 34.1)
for i in range(2):
    add(sfx, bloop(.3, 300 + 80 * i, 1100), 35.95 + i * .08, pan=-.25 + .5 * i)


# ---------------------------------------------------------------- voz e mix
# eco dramatico em "Sua empresa ja te avisa." e "MovCode."
vo, voice_mono = voz(cues['vo'], HERE, DUR, eco=('L03', 'L11'))
master(music, drums, sfx, send_big, send_plate, vo, voice_mono, kick_times, fim=37.2, out=os.path.join(HERE, 'out'))

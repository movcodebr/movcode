"""Trilha, efeitos e mixagem do Reels "5 sinais" da MovCode.

Tudo sintetizado (os instrumentos ficam em ../../audio/sintese.py): 100 BPM, re menor
(Dm - Bb - F - C). Gera stems (music.wav, sfx.wav, vo.wav) e mix.wav, em 48 kHz estereo.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'audio'))
from sintese import *  # noqa: E402,F401,F403

DUR = 36.6
FIM = 36.0

cues = json.load(open(os.path.join(HERE, '..', 'cues.json')))
T = [4.8, 9.6, 14.4, 19.2, 24.0]          # inicio de cada sinal (2 compassos)
TICK = [t + 3.95 for t in T]              # caixinha marcada

music = bus(DUR)
drums = bus(DUR)
sfx = bus(DUR)
send_big = bus(DUR)
send_plate = bus(DUR)
kick_times = []

CH = {
    'Dm': [nm('A3'), nm('D4'), nm('F4'), nm('A4')],
    'Bb': [nm('A#3'), nm('D4'), nm('F4'), nm('A#4')],
    'F': [nm('A3'), nm('C4'), nm('F4'), nm('A4')],
    'C': [nm('G3'), nm('C4'), nm('E4'), nm('G4')],
}
ROOT = {'Dm': nm('D2'), 'Bb': nm('A#1'), 'F': nm('F1'), 'C': nm('C2')}
ARP = {
    'Dm': ['D5', 'F5', 'A5', 'D6', 'A5', 'F5', 'A5', 'C6'],
    'Bb': ['A#4', 'D5', 'F5', 'A#5', 'F5', 'D5', 'F5', 'A5'],
    'F': ['C5', 'F5', 'A5', 'C6', 'A5', 'F5', 'A5', 'G5'],
    'C': ['C5', 'E5', 'G5', 'C6', 'G5', 'E5', 'G5', 'D6'],
}
PROG = [['Dm', 'Bb'], ['F', 'C']]


def groove(t0, bars, chords, level=1.0, claps=True, stabs=True, arps=True, hats=True, perc=True, open_hats=True):
    """Compassos de 2,4 s; chords: um par [meia barra 1, meia barra 2] por compasso."""
    for b in range(bars):
        tb = t0 + b * 2.4
        for half in range(2):
            name = chords[b][half]
            th = tb + half * 1.2
            add(music, sub(ROOT[name], 1.15, .6 * level), th)
            if stabs:
                for s16 in [0, 3, 6]:
                    add(music, chord_stab(CH[name], 0.11 if s16 else 0.2, g=.26 * level, cutoff=4400), th + s16 * 0.15)
            if arps:
                for i in range(8):
                    add(music, pluck(nm(ARP[name][i]), .1 * level, dec=.18), th + i * 0.15, pan=(-.4 if i % 2 else .4))
            add(music, pad(CH[name], 1.15, g=.08 * level, cutoff=2000, att=.15, rel=.3, seed=int(th * 10)), th)
        for s in range(16):
            ts = tb + s * 0.15
            if s % 4 == 0:
                add(drums, kick(.92 * level), ts)
                kick_times.append(ts)
            if claps and s in (4, 12):
                add(drums, clap(.45 * level), ts)
                add(send_plate, clap(.22 * level), ts)
            if perc and s in (3, 7, 10, 14):
                add(drums, rim(.15 * level), ts, pan=-.25)
            if hats:
                if open_hats and s % 4 == 2:
                    add(drums, hat(.2 * level, .13), ts, pan=.2)
                elif s % 2 == 1:
                    add(drums, hat(.08 * level, .022), ts, pan=-.3)


# ---------------------------------------------------------------- abertura (0 – 4.8)
add(sfx, whoosh(.38, .5, 200, 5000, rev=True, pan_sweep=False), 0.0)      # succao antes do "5"
add(sfx, impact(.75), 0.37)
add(send_big, impact(.35, bright=1.2), 0.37)
add(drums, crash(.25, 2.2), 0.37)
add(send_big, chord_stab(CH['Dm'], .5, g=.3, cutoff=3000, dec=.4), 0.37)
add(music, pad(CH['Dm'], 2.0, g=.16, cutoff=900, att=.3, rel=.4, seed=1), 0.37)
add(music, pad(CH['Bb'], 2.0, g=.16, cutoff=1100, att=.4, rel=.4, seed=2), 2.4)
add(music, sub(ROOT['Dm'], 2.0, .45), 0.37)
add(music, sub(ROOT['Bb'], 2.0, .45), 2.4)
# relogio: semicolcheias abafadas e arpejo filtrado crescendo
for i in range(int((4.8 - 0.6) / 0.15)):
    ts = 0.6 + i * 0.15
    k = (ts - 0.6) / 4.2
    add(drums, hat(.05 + .07 * k, .02), ts, pan=(-.3 if i % 2 else .3))
    name = 'Dm' if ts < 2.4 else 'Bb'
    add(music, lp(pluck(nm(ARP[name][i % 8]), .09 * k, dec=.15), 1200 + 4000 * k), ts, pan=(-.35 if i % 2 else .35))
for ts in [2.4, 3.0, 3.6, 4.2]:
    add(drums, kick(.45), ts)
    kick_times.append(ts)
# palavras chegando
for ti in [0.78, 1.57, 2.12, 2.87]:
    add(sfx, whoosh(.22, .12, 800, 4000), ti - .1)
# celula da planilha selecionada em "planilha."
add(sfx, blip(nm('C6'), .25, .05), 3.39)
add(sfx, blip(nm('G6'), .18, .05), 3.47, pan=.3)
add(sfx, pop(.3, 1400, 600, .03), 3.6)
# caixinhas do checklist
for i in range(5):
    add(sfx, blip(nm('D6') + [0, 2, 3, 5, 7][i], .12, .05), 3.92 + i * .07, pan=-.4 + .2 * i)
add(music, riser(1.2, .26, pitch=(nm('D4'), nm('D6'))), 3.6)

# ---------------------------------------------------------------- sinais (4.8 – 28.8)
for i, t0 in enumerate(T):
    lvl = [.8, .9, 1.0, 1.0, 1.0][i]
    groove(t0, 2, PROG, level=lvl, claps=i > 0, perc=i > 1, open_hats=i > 0)
    add(sfx, whoosh(.4, .45), t0 - .2)
    add(sfx, impact(.3, f0=70, sub_dec=.35), t0)
    if i == 0:
        add(drums, crash(.3), t0)
        add(send_big, crash(.12), t0)
    # caixinha marcada: plim de dois sinos + estalo
    add(sfx, ding(1568, 2093, .32), TICK[i], pan=-.2)
    add(sfx, pop(.3, 1100, 500, .03), TICK[i])
    add(send_big, bell(2093, .08, .5), TICK[i] + .08)

rng2 = np.random.default_rng(21)

# 1: planilha — celulas, nome do arquivo digitado, erros, etiqueta
for _ in range(26):
    add(sfx, click(.1 + .08 * rng2.random()), 5.25 + rng2.random() * 1.6, pan=rng2.uniform(-.5, .5))
for t0, n in [(5.95, 6), (6.45, 3), (6.95, 10)]:
    for j in range(n):
        add(sfx, click(.22), t0 + j / 60 + rng2.random() * .006, pan=.15)
for te in [6.25, 6.6, 7.0, 7.25]:
    add(sfx, lp(blip(nm('D3'), .25, .07), 900), te, pan=rng2.uniform(-.4, .4))
    add(sfx, lp(blip(nm('C#3'), .18, .06), 900), te + .06)
add(sfx, pop(.35, 800, 300, .05), 7.45)
add(sfx, click(.3), 7.62, pan=.3)

# 2: digita duas vezes — mensagem, teclado, erro, carimbo "2x"
add(sfx, bloop(.4, 500, 1200), 10.0, pan=-.3)
add(sfx, whoosh(.25, .18, 600, 3000), 10.45)
add(sfx, whoosh(.25, .18, 600, 3000), 11.5)


def typing(t0, n, cps=30):
    for j in range(n):
        add(sfx, click(.2 + .1 * rng2.random()), t0 + j / cps + rng2.uniform(0, .01), pan=rng2.uniform(-.2, .2))
        if rng2.random() < .25:
            add(sfx, lp(click(.12), 3000), t0 + j / cps + .015)


typing(10.85, 24)
typing(11.95, 23)
add(sfx, lp(blip(nm('A#2'), .3, .1), 800), 12.8)          # erro de digitacao
add(sfx, impact(.45, f0=80, sub_dec=.35, bright=1.3), 12.95)
add(sfx, pop(.4, 500, 120, .08), 12.95)
add(sfx, pop(.3, 1200, 500, .03), 13.2, pan=-.3)

# 3: numeros — balao, resposta, relogio
add(sfx, whoosh(.25, .18, 500, 2500), 14.85)
add(sfx, bloop(.38, 450, 1100), 15.45, pan=-.3)
add(sfx, bloop(.38, 650, 1500), 16.5, pan=.3)
add(sfx, pop(.3, 1000, 450, .03), 16.95)
for j in range(int((18.35 - 17.0) / .25)):
    tk = 17.0 + j * .25
    add(sfx, rim(.16 if j % 2 == 0 else .1), tk, pan=-.2 if j % 2 else .2)
for th in [17.0 + 1.3 / 3, 17.0 + 2.6 / 3, 18.3]:
    add(sfx, blip(nm('A3'), .14, .08), th)

# 4: crescer = contratar — clientes chegando, contratacoes
for j in range(3):
    add(sfx, whoosh(.22, .14, 600, 3000), 19.55 + j * .12)
for j in range(10):
    add(sfx, blip(nm('D5') + [0, 2, 3, 5, 7, 9, 10, 12, 14, 15][j], .13, .06), 20.4 + j * .22, pan=-.5 + .1 * j)
for th in [21.3, 22.3]:
    add(sfx, bloop(.4, 300, 800), th)
    add(sfx, bell(1318.5, .14, .35), th + .06)

# 5: site — celular, zeros, teia, bola de feno
add(sfx, whoosh(.3, .2, 400, 2500), 24.4)
for th in [25.15, 25.35]:
    add(sfx, lp(pop(.35, 300, 120, .06), 1200), th, pan=.3)
add(sfx, bell(4186, .04, .6), 25.7, pan=.4)
add(sfx, bell(3520, .03, .7), 25.8, pan=.3)
add(sfx, pop(.3, 1000, 450, .03), 26.4, pan=.3)
n = int(1.8 * FS)
tw = svf(noise(n), 500 + 700 * np.sin(np.pi * tt(n) / 1.8), 1.4, 1) * np.sin(np.pi * tt(n) / 1.8) ** 2
add(sfx, np.stack([tw, np.roll(tw, 500)], 1) * .5, 26.2)  # vento
for tb in [26.3, 26.83, 27.37, 27.9]:
    add(sfx, lp(pop(.25, 220, 90, .05), 600), tb, pan=-.6 + .6 * (tb - 26.3) / .8)

# ---------------------------------------------------------------- recapitulacao + "bora" (28.8 – 31.2)
add(music, pad(CH['F'], 1.2, g=.18, cutoff=1500, att=.05, rel=.3, seed=7), 28.8)
add(music, pad(CH['C'], 1.2, g=.18, cutoff=1700, att=.05, rel=.3, seed=8), 30.0)
add(music, sub(ROOT['F'], 1.15, .5), 28.8)
add(music, sub(ROOT['C'], 1.15, .5), 30.0)
add(drums, kick(.8), 28.8)
kick_times.append(28.8)
add(drums, crash(.18), 28.8)
for i in range(5):
    add(sfx, whoosh(.2, .1, 800, 3500), 28.75 + i * .05)
    add(sfx, pop(.18, 900 + 120 * i, 400, .03), 29.05 + i * .07, pan=-.3 + .15 * i)
add(sfx, impact(.3, f0=75, sub_dec=.3), 29.18)
add(sfx, blip(nm('D6'), .2, .08), 29.18)
for j in range(3):  # "digitando..."
    add(sfx, blip(nm('A5'), .05, .04), 29.97 + j * .06)
add(sfx, bloop(.4, 400, 1000), 30.15)
# virada acelerando ate a volta
tb, rolls = 30.0, []
while tb < 31.18:
    k = (tb - 30.0) / 1.2
    rolls.append((tb, .18 + .5 * k))
    tb += 0.15 if k < .5 else (0.075 if k < .8 else 0.0375)
for tb, g in rolls:
    add(drums, snare(g * .5, dec=.08), tb)
add(music, riser(1.15, .3, pitch=(nm('C4'), nm('C6'))), 30.05)

# ---------------------------------------------------------------- marca + CTA (31.2 – 36.0)
add(sfx, impact(.7), 31.2)
add(send_big, impact(.35, bright=1.2), 31.2)
add(drums, crash(.35, 2.0), 31.2)
add(send_big, crash(.15), 31.2)
groove(31.2, 1, [['Dm', 'Bb']], level=.95)
groove(33.6, 1, [['F', 'C']], level=.7, claps=False, perc=False, stabs=False)
add(music, chord_stab(CH['Dm'] + [nm('D5')], .9, g=.38, cutoff=5000, dec=.5), 31.2)
# acorde final em re maior (picardia) no fim do compasso
D_MAJ = [nm('A3'), nm('D4'), nm('F#4'), nm('A4'), nm('D5')]
add(music, chord_stab(D_MAJ, 1.2, g=.36, cutoff=5200, dec=.7), 35.4)
add(music, sub(ROOT['Dm'], 1.0, .5), 35.4)
add(drums, kick(.9), 35.4)
kick_times.append(35.4)
add(send_big, chord_stab(D_MAJ, 1.2, g=.22, cutoff=4000, dec=.7), 35.4)
# brilhos do logo
r3 = np.random.default_rng(5)
for i in range(22):
    add(sfx, bell(r3.uniform(2500, 6000), .03, .25), 31.25 + r3.uniform(0, .9) ** 1.5, pan=r3.uniform(-.9, .9))
for j in range(2):
    add(sfx, bloop(.3, 300 + 80 * j, 900), 31.25 + j * .07, pan=-.25 + .5 * j)
add(sfx, whoosh(.35, .18, 800, 5000), 31.4)
add(sfx, bloop(.35, 420, 900), 31.75)
add(sfx, pop(.2, 900, 400), 32.6)
add(sfx, pop(.28, 1100, 450), 33.3)
add(sfx, pop(.25, 1000, 400), 34.5)

# ---------------------------------------------------------------- voz e mix
vo, voice_mono = voz(cues['vo'], HERE, DUR)
# a trilha toca por baixo de todos os sinais: um pouco abaixo do primeiro Reels (0,16)
master(music, drums, sfx, send_big, send_plate, vo, voice_mono, kick_times, fim=FIM, out=os.path.join(HERE, 'out'), G_M=0.14)

"""Narracao dos Reels com o Gemini TTS (Google).

Precisa da variavel de ambiente GEMINI_API_KEY (chave gratuita em
https://aistudio.google.com/apikey). Le o roteiro (falas e direcao de voz) de
<pasta>/roteiro.json e os tempos de <pasta>/cues.json; gera <pasta>/audio/L*.wav
e <pasta>/audio/vo.json no lugar da voz atual (a anterior vai para
<pasta>/audio/vozes/anterior/). A pasta padrao e a do primeiro Reels (video-reels/).

uso:
    python3 audio/gemini_vo.py [VOZ] [--pasta DIR]            # roteiro inteiro (padrao: Sulafat)
    python3 audio/gemini_vo.py --amostras V1,V2 [--pasta DIR] # amostra curta de cada voz em audio/amostras/
    python3 audio/gemini_vo.py VOZ --bruto audio/vozes/gemini-VOZ-bruto.wav
                                                   # corta de novo um audio ja gerado, sem chamar a API

Vozes femininas boas para locucao: Sulafat (calorosa), Kore (firme), Laomedeia (animada),
Aoede (leve). Masculinas: Puck (animado), Achird (amigavel), Charon (informativo), Orus (firme).
Modelo: o mais novo com "tts" no nome; force outro com GEMINI_TTS_MODEL.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

import numpy as np
import soundfile as sf

API = 'https://generativelanguage.googleapis.com/v1beta'
KEY = os.environ.get('GEMINI_API_KEY', '').strip()
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def roteiro(pasta):
    r = json.load(open(os.path.join(pasta, 'roteiro.json')))
    return list(r['falas'].items()), '\n'.join(r['direcao']) + '\n', r


def need_key():
    if not KEY:
        sys.exit('GEMINI_API_KEY não está definida. Crie a chave em https://aistudio.google.com/apikey '
                 'e adicione-a como variável de ambiente nas configurações do ambiente.')


def call(path, body=None, tries=6):
    url = f'{API}/{path}'
    data = json.dumps(body).encode() if body is not None else None
    for i in range(tries):
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json', 'x-goog-api-key': KEY})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:400]
            if e.code in (429, 500, 503) and i < tries - 1:
                wait = 20 * (i + 1)
                print(f'  {e.code}, tentando de novo em {wait}s: {msg[:120]}')
                time.sleep(wait)
                continue
            sys.exit(f'Erro {e.code} da API: {msg}')


def pick_model():
    if os.environ.get('GEMINI_TTS_MODEL'):
        return os.environ['GEMINI_TTS_MODEL']
    models = call('models?pageSize=1000').get('models', [])
    tts = [m['name'].split('/')[-1] for m in models if 'tts' in m['name'] and 'generateContent' in m.get('supportedGenerationMethods', [])]
    if not tts:
        sys.exit('Nenhum modelo TTS disponível para esta chave.')
    # preferencia: flash (nao lite/pro), versao mais alta
    def score(n):
        import re
        v = re.findall(r'(\d+(?:\.\d+)?)', n)
        ver = float(v[0]) if v else 0
        return (('flash' in n) and ('lite' not in n), ver, 'preview' not in n)
    tts.sort(key=score, reverse=True)
    print('modelos TTS:', ', '.join(tts), '->', tts[0])
    return tts[0]


def tts(model, text, voice):
    body = {
        'contents': [{'parts': [{'text': text}]}],
        'generationConfig': {
            'responseModalities': ['AUDIO'],
            'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice}}},
        },
    }
    r = call(f'models/{model}:generateContent', body)
    part = r['candidates'][0]['content']['parts'][0]['inlineData']
    rate = 24000
    for tok in part.get('mimeType', '').split(';'):
        if tok.strip().startswith('rate='):
            rate = int(tok.split('=')[1])
    pcm = np.frombuffer(base64.b64decode(part['data']), dtype='<i2').astype(np.float32) / 32768
    return pcm, rate


def envelope(x, sr, hop=0.01):
    h = int(sr * hop)
    n = len(x) // h
    return np.sqrt(np.mean(x[:n * h].reshape(n, h) ** 2, axis=1))


def flatness(x):
    s = np.abs(np.fft.rfft(x * np.hanning(len(x)))) + 1e-9
    return np.exp(np.mean(np.log(s))) / np.mean(s)


def strip_junk(x, sr):
    """Tira das pontas cliques e rajadas de ruido isoladas por silencio.

    O Gemini as vezes devolve um clique no inicio e um chiado em volume maximo
    no fim do audio. Sao 'ilhas' de som separadas da fala por mais de 100 ms:
    o clique dura ate 30 ms; o chiado, ate 150 ms, com espectro de ruido
    (planicidade > 0,7; nas consoantes da fala fica abaixo de 0,65)."""
    env = envelope(x, sr)
    if not len(env):
        return x
    on = np.append(env >= 0.03 * env.max(), False)
    runs, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        if not v and start is not None:
            runs.append((start, i))
            start = None
    h = int(sr * 0.01)

    def junk(r, gap):
        d = r[1] - r[0]
        return gap >= 10 and (d <= 3 or (d <= 15 and flatness(x[r[0] * h:r[1] * h]) > 0.7))
    a, b = 0, len(runs)
    while b - a > 1 and junk(runs[a], runs[a + 1][0] - runs[a][1]):
        a += 1
    while b - a > 1 and junk(runs[b - 1], runs[b - 1][0] - runs[b - 2][1]):
        b -= 1
    i0 = (runs[a - 1][1] + 1) * h if a else 0
    i1 = (runs[b][0] - 1) * h if b < len(runs) else len(x)
    return x[i0:i1]


def trim(x, sr):
    x = strip_junk(x, sr)
    thr = 0.02 * np.max(np.abs(x))
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    x = x[max(0, idx[0] - int(.005 * sr)): idx[-1] + int(.1 * sr)].copy()
    f = int(.004 * sr)  # rampas curtas para o corte nao estalar
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    return x


def split_lines(x, sr, n):
    """Corta nos n-1 silencios mais longos."""
    env = envelope(x, sr)
    sil = env < 0.03 * env.max()
    runs, start = [], None
    for i, s in enumerate(sil):
        if s and start is None:
            start = i
        if not s and start is not None:
            if i - start >= 18 and start > 0:
                runs.append((i - start, start, i))
            start = None
    if len(runs) < n - 1:
        return None
    cuts = sorted(sorted(runs, reverse=True)[:n - 1], key=lambda r: r[1])
    pts = [0] + [int((a + b) / 2 * 0.01 * sr) for _, a, b in cuts] + [len(x)]
    segs = [trim(x[pts[i]:pts[i + 1]], sr) for i in range(n)]
    if any(not (0.35 < len(s) / sr < 4.5) for s in segs):
        return None
    return segs


def fit(seg, sr, maxdur):
    d = len(seg) / sr
    if d <= maxdur:
        return seg
    tempo = min(d / maxdur, 1.25)
    tmp_in, tmp_out = '/tmp/_gvo_in.wav', '/tmp/_gvo_out.wav'
    sf.write(tmp_in, seg, sr)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', tmp_in, '-af', f'rubberband=tempo={tempo:.4f}', tmp_out], check=True)
    out, _ = sf.read(tmp_out)
    print(f'    acelerado {tempo:.2f}x para caber ({d:.2f}s -> {len(out) / sr:.2f}s)')
    return out


def main():
    args = sys.argv[1:]
    opt = {}
    for k in ('--bruto', '--pasta'):
        if k in args:
            i = args.index(k)
            opt[k] = args[i + 1]
            del args[i:i + 2]
    bruto = opt.get('--bruto')
    pasta = os.path.abspath(opt.get('--pasta', RAIZ))
    out = os.path.join(pasta, 'audio')
    LINES, DIRECAO, rot = roteiro(pasta)
    if args and args[0] == '--amostras':
        need_key()
        model = pick_model()
        voices = args[1].split(',')
        os.makedirs(os.path.join(out, 'amostras'), exist_ok=True)
        texto = DIRECAO + '\n'.join(t for _, t in LINES[:6])
        for v in voices:
            x, sr = tts(model, texto, v)
            sf.write(os.path.join(out, 'amostras', f'{v}.wav'), x, sr)
            print('amostra', v, round(len(x) / sr, 1), 's')
            time.sleep(8)
        return

    voice = args[0] if args else 'Sulafat'
    cues = json.load(open(os.path.join(pasta, 'cues.json')))['vo']
    order = sorted(cues, key=cues.get)
    slot = {}
    for i, k in enumerate(order):
        nxt = cues[order[i + 1]] if i + 1 < len(order) else rot['fim_da_voz']
        slot[k] = nxt - cues[k] - 0.05
    slot.update(rot.get('maximo', {}))

    os.makedirs(os.path.join(out, 'vozes'), exist_ok=True)
    if bruto:
        # reaproveita um audio ja gerado (sem chamar a API)
        x, sr = sf.read(bruto)
        old = json.load(open(os.path.join(out, 'vo.json')))
        model = next((m['model'] for m in old.values() if m.get('model')), '?')
    else:
        need_key()
        model = pick_model()
        print(f'gerando o roteiro inteiro com {voice}...')
        x, sr = tts(model, DIRECAO + '\n'.join(t for _, t in LINES), voice)
        sf.write(os.path.join(out, 'vozes', f'gemini-{voice}-bruto.wav'), x, sr)
    segs = split_lines(x, sr, len(LINES))
    if segs is None and bruto:
        sys.exit('não deu para separar as falas desse áudio pelo silêncio.')
    if segs is None:
        print('não deu para separar as falas pelo silêncio; gerando uma por uma...')
        segs = []
        for key, text in LINES:
            y, sr = tts(model, DIRECAO + text, voice)
            segs.append(trim(y, sr))
            time.sleep(8)

    prev = os.path.join(out, 'vozes', 'anterior')
    os.makedirs(prev, exist_ok=True)
    for key, _ in LINES:
        f = os.path.join(out, f'{key}.wav')
        if os.path.exists(f):
            shutil.copy(f, prev)
    meta = {}
    for (key, text), seg in zip(LINES, segs):
        seg = fit(seg, sr, slot[key])
        sf.write(os.path.join(out, f'{key}.wav'), seg, sr)
        meta[key] = {'text': text, 'voice': voice, 'model': model, 'dur': round(len(seg) / sr, 3)}
        print(f'  {key:5s} {meta[key]["dur"]:5.2f}s (cabe {slot[key]:.2f}s)  {text}')
    json.dump(meta, open(os.path.join(out, 'vo.json'), 'w'), ensure_ascii=False, indent=1)
    print('pronto. Agora: python3 audio/synth.py e ../encode_web.sh (veja o README)')


if __name__ == '__main__':
    main()

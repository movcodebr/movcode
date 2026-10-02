"""Narracao offline com Kokoro (voz sintetica, soa robotica; serve de rascunho).

Precisa de kokoro-v1.0.onnx e voices-v1.0.bin em KOKORO_DIR (padrao: ./modelos):
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
uso: python3 audio/kokoro_vo.py [pf_dora|pm_alex|pm_santa]
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.environ.get('KOKORO_DIR', os.path.join(HERE, '..', 'modelos'))
sys.path.insert(0, HERE)
from gemini_vo import LINES  # noqa: E402  (mesmo roteiro)

voice = sys.argv[1] if len(sys.argv) > 1 else 'pf_dora'
k = Kokoro(os.path.join(MOD, 'kokoro-v1.0.onnx'), os.path.join(MOD, 'voices-v1.0.bin'))
meta = {}
for key, text in LINES:
    # "MovCode" foneticamente, senao vira "Mov Cóji"
    ph = 'mˌɔvkˈowdʒi.' if key == 'L11' else k.tokenizer.phonemize(text, 'pt-br')
    a, sr = k.create(ph, voice=voice, speed=1.0, is_phonemes=True)
    idx = np.where(np.abs(a) > 0.01 * np.max(np.abs(a)))[0]
    a = a[max(0, idx[0] - 240): idx[-1] + 2400]
    sf.write(os.path.join(HERE, f'{key}.wav'), a, sr)
    meta[key] = {'text': text, 'voice': voice, 'ph': ph, 'dur': round(len(a) / sr, 3)}
    print(key, meta[key]['dur'], text)
json.dump(meta, open(os.path.join(HERE, 'vo.json'), 'w'), ensure_ascii=False, indent=1)

# Reels da MovCode

Vídeo de apresentação da MovCode para o Instagram: 37,2 s, 1080×1920, 30 fps.
Animação em HTML/CSS/GSAP renderizada quadro a quadro no Chromium. A trilha e
os efeitos sonoros são sintetizados em Python (nada de samples), e a montagem
final é feita no ffmpeg.

Esta pasta não faz parte do site: fica só neste branch (`claude/reels-movcode`)
e o GitHub Pages continua publicando a partir do `main`.

## Estado atual

Animação, trilha, mixagem e narração prontas. A narração é do **Gemini TTS**
(voz feminina Sulafat, modelo `gemini-3.8-flash-tts`), gerada de uma vez só a
partir do roteiro e cortada nos silêncios em 16 falas. As vozes offline
(Kokoro) ficam guardadas em `audio/vozes/`.

Para gerar o vídeo do zero (precisa da variável de ambiente `GEMINI_API_KEY`
só para refazer a voz; a chave é gratuita em https://aistudio.google.com/apikey
e fica nas configurações do ambiente, nunca no código nem no chat):

```bash
cd video-reels
python3 audio/gemini_vo.py --amostras Sulafat,Kore,Laomedeia,Puck   # opcional: compara vozes
python3 audio/gemini_vo.py Sulafat      # gera as 16 falas, corta e encaixa nos tempos
python3 audio/synth.py                  # trilha + efeitos + voz -> audio/out/mix.wav
node render.js frames 60 0 37.2 4       # ~10 min, 2.232 quadros (só na primeira vez)
./encode_web.sh frames entrega/movcode-reels.mp4
```

O Gemini às vezes devolve um clique no começo e um chiado em volume máximo no
fim do áudio; o `gemini_vo.py` remove essas sobras sozinho. O áudio bruto fica
em `audio/vozes/gemini-<voz>-bruto.wav` (fora do git) e pode ser cortado de
novo sem chamar a API: `python3 audio/gemini_vo.py Sulafat --bruto
audio/vozes/gemini-Sulafat-bruto.wav`.

## Roteiro (4 atos, 100 BPM)

Os tempos das falas ficam em `cues.json` e são a referência comum da animação
(`scene.html`) e do áudio (`audio/synth.py`).

| Tempo | Cena | Narração |
| --- | --- | --- |
| 0,0 | Ponto laranja pulsando | Todo negócio começa pequeno. |
| 2,4 | Caos: caderno do fiado, planilhas, estoque, enxurrada de mensagens | O fiado no caderno. / A planilha com três versões. / O estoque que nunca bate. |
| 8,4 | Título | Sua empresa já te avisa. |
| 10,8 | Bolha da MovCode | Bora resolver isso de vez? |
| 13,2 | Sites (fundo laranja) | Sites que colocam você no mapa. |
| 15,6 | Lojas virtuais | Lojas que vendem até de madrugada. |
| 18,0 | Sistemas de gestão (fundo claro) | Sistemas que arrumam a casa. |
| 20,4 | Automações | Automações que trabalham sozinhas. |
| 22,8 | Painéis (+38%) | — |
| 24,0 | Cidade crescendo | Do mercadinho… / à indústria. |
| 26,4 | "tamanhoooo" | Tecnologia do tamanho do seu negócio. |
| 30,0 | Logo + CTA | MovCode. / Agende seu diagnóstico grátis. / Link na bio. |

## Arquivos

```
video-reels/
├── scene.html        animação inteira (GSAP); window.__seek(t) desenha o instante t
├── render.js         captura os quadros com Playwright (vários processos em paralelo)
├── encode.sh         pós-produção + H.264 (motion blur, bloom, vinheta, grão, aberração)
├── encode_web.sh     igual, limitado a ~6 Mbps (arquivo < 30 MB)
├── ca.cmd            pulsos de aberração cromática nos impactos (sendcmd do ffmpeg)
├── cues.json         tempos das falas
├── fonts.css, fonts/ Bricolage Grotesque, Figtree, JetBrains Mono e Caveat (licença OFL)
├── audio/
│   ├── synth.py      trilha, efeitos, tratamento da voz, mixagem e master (−14 LUFS)
│   ├── gemini_vo.py  narração com Gemini TTS
│   ├── kokoro_vo.py  narração offline com Kokoro (rascunho)
│   ├── L*.wav        falas em uso (hoje: Gemini, voz Sulafat)
│   └── vozes/        versões de voz guardadas
└── entrega/          capa do Reels; os .mp4 gerados ficam aqui (fora do git)
```

O GSAP vem do próprio site (`../assets/js/vendor/gsap.min.js`).

## Requisitos

- Node 18+ e `npm install` nesta pasta (playwright-core).
- Chromium: o caminho padrão é o do ambiente de nuvem do Claude Code; em outra
  máquina, defina `CHROME_PATH`.
- Python 3.10+ com `numpy scipy soundfile numba pyloudnorm`.
- ffmpeg com `rubberband`, `tmix`, `rgbashift` e `libx264`.

## Ajustes rápidos

- **Uma cena:** prévia de instantes avulsos com
  `node render.js --stills stills 13.5,21.9` e, depois da alteração, apague e
  renderize só o trecho: `node render.js frames 60 <de> <até> 4` (o script pula
  os quadros que já existem).
- **Tempo de uma fala:** altere `cues.json`. O áudio segue sozinho; na
  animação, confira os tempos das palavras da cena em `scene.html`.
- **Volume da trilha sob a voz:** `G_M` e `duck` em `audio/synth.py`.

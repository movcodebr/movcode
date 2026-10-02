# Reels da MovCode

Vídeos da MovCode para o Instagram: 1080×1920, 30 fps. Animação em HTML/CSS/GSAP
renderizada quadro a quadro no Chromium. A trilha e os efeitos sonoros são
sintetizados em Python (nada de samples), a narração é do Gemini TTS e a
montagem final é feita no ffmpeg.

Esta pasta não faz parte do site: fica só neste branch e o GitHub Pages continua
publicando a partir do `main`.

| Pasta | Reels | Duração | Vídeo, capa e legenda |
| --- | --- | --- | --- |
| `.` | Apresentação: "Tecnologia do tamanho do seu negócio" | 37,2 s | `entrega/movcode-reels.mp4` |
| `sinais/` | "5 sinais de que sua empresa já passou da planilha" | 36,0 s | `sinais/entrega/movcode-5-sinais.mp4` |

Os dois usam a voz feminina Sulafat (modelo `gemini-3.8-flash-tts`), gerada de
uma vez só a partir do roteiro e cortada nos silêncios. As vozes offline do
primeiro Reels (Kokoro) ficam guardadas em `audio/vozes/`.

## Como gerar

A variável de ambiente `GEMINI_API_KEY` só é necessária para refazer a voz (a
chave é gratuita em https://aistudio.google.com/apikey e fica nas configurações
do ambiente, nunca no código nem no chat). Tudo roda de dentro de `video-reels/`.

Primeiro Reels:

```bash
python3 audio/gemini_vo.py --amostras Sulafat,Kore,Laomedeia,Puck   # opcional: compara vozes
python3 audio/gemini_vo.py Sulafat      # gera as falas, corta e encaixa nos tempos
python3 audio/synth.py                  # trilha + efeitos + voz -> audio/out/mix.wav
node render.js frames 60 0 37.2 4       # ~10 min, 2.232 quadros (só na primeira vez)
./encode_web.sh frames entrega/movcode-reels.mp4
node capa.js                            # capa -> entrega/movcode-reels-capa.jpg
```

"5 sinais" (as mesmas ferramentas, apontadas para a pasta `sinais/`):

```bash
python3 audio/gemini_vo.py Sulafat --pasta sinais
python3 sinais/audio/synth.py
node render.js --cena sinais/scene.html sinais/frames 60 0 36 4
(cd sinais && ../encode_web.sh frames entrega/movcode-5-sinais.mp4)
node capa.js sinais/entrega/movcode-5-sinais-capa.jpg --capa sinais/capa.html
```

O Gemini às vezes devolve um clique no começo e um chiado em volume máximo no
fim do áudio; o `gemini_vo.py` remove essas sobras sozinho. O áudio bruto fica
em `<pasta>/audio/vozes/gemini-<voz>-bruto.wav` (fora do git) e pode ser cortado
de novo sem chamar a API: `python3 audio/gemini_vo.py Sulafat --bruto
audio/vozes/gemini-Sulafat-bruto.wav` (com `--pasta sinais` para o segundo).

## Novo Reels

A logo da MovCode (os dois bonecos laranja) aparece sempre **sem olhos**, em
qualquer vídeo ou capa.

Crie uma pasta ao lado de `sinais/` com `roteiro.json` (falas e direção da voz),
`cues.json` (tempo de cada fala), `scene.html` (com `window.__ready` e
`window.__seek(t)`), `ca.cmd`, `capa.html` e `audio/synth.py` (importa
`audio/sintese.py`, compõe a trilha e chama `voz()` e `master()`).

## Roteiro do primeiro Reels (4 atos, 100 BPM)

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

## Roteiro do "5 sinais" (100 BPM, 2 compassos por sinal)

Lista com um checklist fixo no topo: cada sinal marca uma caixinha e, no fim,
as caixinhas viram a lista de recapitulação ("Marcou 2 ou mais?"). Re menor
(Dm – B♭ – F – C), fechando em ré maior.

| Tempo | Cena | Narração |
| --- | --- | --- |
| 0,0 | "5 sinais", com "planilha." numa célula selecionada; checklist aparece | Cinco sinais de que a sua empresa já passou da planilha. |
| 4,8 | 1 · planilha `estoque_FINAL_agora_vai.xlsx` e "Só a Bia sabe mexer" | Um: tudo vive numa planilha que só uma pessoa entende. |
| 9,6 | 2 · pedido do WhatsApp digitado duas vezes, com erro, e carimbo "2x" | Dois: você digita a mesma informação duas vezes. |
| 14,4 | 3 · "Como foi o mês?", relatório e horas paradas | Três: pra saber como foi o mês, alguém precisa parar tudo. |
| 19,2 | 4 · clientes, horas de trabalho manual e contratações subindo juntos | Quatro: cada cliente novo vira mais trabalho manual. |
| 24,0 | 5 · site sem mensagens, teia e bola de feno | Cinco: o site existe, mas não traz cliente. |
| 28,8 | Recapitulação "Marcou 2 ou mais?" | Marcou dois ou mais? |
| 30,0 | Balão da MovCode | Bora resolver isso de vez? |
| 31,2 | Logo + CTA + "Comenta quantos você marcou" | Agende seu diagnóstico grátis na MovCode. Link na bio. |

## Arquivos

```
video-reels/
├── scene.html        animação do primeiro Reels (GSAP); window.__seek(t) desenha o instante t
├── roteiro.json      falas e direção da voz
├── cues.json         tempos das falas
├── ca.cmd            pulsos de aberração cromática nos impactos (sendcmd do ffmpeg)
├── capa.html         capa do Reels (o essencial fica no recorte 3:4 da grade do perfil)
├── render.js         captura os quadros com Playwright (vários processos; --cena para outro Reels)
├── capa.js           renderiza a capa em JPG (--capa para outro Reels)
├── encode.sh         pós-produção + H.264 (motion blur, bloom, vinheta, grão, aberração)
├── encode_web.sh     igual, limitado a ~6 Mbps (arquivo < 30 MB); usa o ca.cmd da pasta atual
├── fonts.css, fonts/ Bricolage Grotesque, Figtree, JetBrains Mono e Caveat (licença OFL)
├── audio/
│   ├── sintese.py    instrumentos, efeitos, tratamento da voz e master (−14 LUFS), comuns aos Reels
│   ├── synth.py      trilha e efeitos do primeiro Reels
│   ├── gemini_vo.py  narração com Gemini TTS (--pasta para outro Reels)
│   ├── kokoro_vo.py  narração offline com Kokoro (rascunho)
│   ├── L*.wav        falas em uso (hoje: Gemini, voz Sulafat)
│   └── vozes/        versões de voz guardadas
├── entrega/          capa e legenda; os .mp4 gerados ficam aqui (fora do git)
└── sinais/           Reels "5 sinais": scene.html, roteiro.json, cues.json, ca.cmd,
                      capa.html, audio/ (synth.py e falas) e entrega/
```

O GSAP vem do próprio site (`assets/js/vendor/gsap.min.js`, na raiz do repositório).

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
  os quadros que já existem). Para o "5 sinais", acrescente `--cena sinais/scene.html`.
- **Tempo de uma fala:** altere o `cues.json` do Reels. O áudio segue sozinho; na
  animação, confira os tempos das palavras da cena no `scene.html`.
- **Volume da trilha sob a voz:** `G_M` na chamada de `master()` no `synth.py` do
  Reels (0,16 no primeiro, 0,14 no "5 sinais") e `duck` em `audio/sintese.py`.

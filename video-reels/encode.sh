#!/bin/bash
# uso: ./encode.sh <frames_dir> <saida.mp4> [audio.wav] [crf]
set -e
FR=$1; OUT=$2; AUD=${3:-audio/out/mix.wav}; CRF=${4:-18}
ffmpeg -y -hide_banner -loglevel warning -stats -thread_queue_size 64 \
  -framerate 60 -i "$FR/f%05d.png" -i "$AUD" \
  -filter_complex "\
[0:v]format=gbrp,tmix=frames=2:weights='1 1',fps=30,\
sendcmd=f=ca.cmd,rgbashift=edge=smear,split[a][b];\
[b]scale=270:480:flags=bilinear,curves=all='0/0 0.62/0 1/1',gblur=sigma=10,scale=1080:1920:flags=bicubic[bl];\
[a][bl]blend=all_mode=screen:all_opacity=0.3,\
vignette=angle=PI/11:mode=forward,\
scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,\
noise=c0s=3:c0f=t[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -preset slow -crf $CRF -maxrate 24M -bufsize 48M -profile:v high -level 4.2 -g 60 -bf 2 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$OUT"

/* -------------------------------------------------------------------------
   Home conceitual: tudo cresce com o scroll.
   Usa GSAP + ScrollTrigger + Lenis (em assets/js/vendor). Se o visitante
   pedir menos movimento, ou se as bibliotecas faltarem, nada disto roda
   e a pagina fica no layout estatico do home.css.
------------------------------------------------------------------------- */
(() => {
    const html = document.documentElement;
    const reduzir = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reduzir || !window.gsap || !window.ScrollTrigger) {
        html.classList.remove('intro-ativa', 'anima-pre');
        return;
    }

    const { gsap, ScrollTrigger } = window;
    gsap.registerPlugin(ScrollTrigger);
    html.classList.add('anima');

    const ponteiroFino = window.matchMedia('(pointer: fine)').matches;

    // ---------- Rolagem suave ----------
    let lenis = null;
    if (window.Lenis) {
        lenis = new window.Lenis({ lerp: 0.1 });
        lenis.on('scroll', ScrollTrigger.update);
        gsap.ticker.add((tempo) => lenis.raf(tempo * 1000));
        gsap.ticker.lagSmoothing(0);

        // Os links de secao (site.js) usam a rolagem suave do Lenis
        window.MOVCODE_ROLAR = (alvo, imediato = false) => lenis.scrollTo(alvo, imediato ? { immediate: true } : { duration: 1.4 });
    }

    // ---------- Divide titulos em palavras ou letras com mascara ----------
    function dividir(el, modo) {
        if (!el || el.dataset.dividido) return el;
        el.dataset.dividido = modo;
        if (!el.getAttribute('aria-label')) {
            el.setAttribute('aria-label', el.textContent.replace(/\s+/g, ' ').trim());
        }
        const percorrer = (no) => {
            [...no.childNodes].forEach((filho) => {
                if (filho.nodeType === Node.TEXT_NODE) {
                    const pedacos = document.createDocumentFragment();
                    filho.textContent.split(/(\s+)/).forEach((parte) => {
                        if (!parte) return;
                        if (/^\s+$/.test(parte)) {
                            pedacos.appendChild(document.createTextNode(' '));
                            return;
                        }
                        const mascara = document.createElement('span');
                        mascara.className = 'm';
                        mascara.setAttribute('aria-hidden', 'true');
                        if (modo === 'letras') {
                            [...parte].forEach((letra) => {
                                const l = document.createElement('span');
                                l.className = 'l';
                                l.textContent = letra;
                                mascara.appendChild(l);
                            });
                        } else {
                            const p = document.createElement('span');
                            p.className = 'p';
                            p.textContent = parte;
                            mascara.appendChild(p);
                        }
                        pedacos.appendChild(mascara);
                    });
                    filho.replaceWith(pedacos);
                } else if (filho.nodeType === Node.ELEMENT_NODE && !filho.classList.contains('duo') && filho.tagName !== 'BR') {
                    percorrer(filho);
                }
            });
        };
        percorrer(el);
        return el;
    }

    // Entrada suave: a peca sobe um pouco enquanto sai do desfoque e aparece.
    // Sem mascara, entao nada fica "cortado ao meio".
    const ENTRADA = { yPercent: 35, opacity: 0, filter: 'blur(12px)' };
    const CHEGADA = { yPercent: 0, opacity: 1, filter: 'blur(0px)', ease: 'power3.out', clearProps: 'filter' };

    function revelar(el, modo, extra = {}) {
        dividir(el, modo);
        const pecas = el.querySelectorAll(modo === 'letras' ? '.l' : '.p');
        const destaques = el.querySelectorAll('em');
        const tl = gsap.timeline({ scrollTrigger: { trigger: el, start: 'top 85%' } });
        tl.fromTo(pecas, ENTRADA, {
            ...CHEGADA,
            duration: 1.2,
            stagger: modo === 'letras' ? 0.03 : 0.06,
            ...extra
        });
        // A faixa de marca-texto se pinta da esquerda para a direita
        if (destaques.length && getComputedStyle(destaques[0]).backgroundImage !== 'none') {
            tl.fromTo(destaques, { backgroundSize: '0% 62%' }, { backgroundSize: '100% 62%', duration: 0.8, ease: 'power2.inOut' }, 0.45);
        }
    }

    // ---------- Hero ----------
    const palavras = gsap.utils.toArray('.h-titulo .p');
    const letrasTamanho = gsap.utils.toArray('.h-titulo .tamanho .l');
    gsap.set(palavras, ENTRADA);
    html.classList.remove('anima-pre');

    const tlHero = gsap.timeline({ paused: true })
        .to(palavras, { ...CHEGADA, duration: 1.4, stagger: 0.08 })
        .from(letrasTamanho, {
            scaleY: 0.3,
            fontWeight: 200,
            transformOrigin: '50% 100%',
            duration: 0.9,
            ease: 'back.out(2.2)',
            stagger: 0.06
        }, 0.35)
        .from('.h-hero-base .wrap > *', { y: 24, autoAlpha: 0, duration: 0.8, ease: 'power3.out', stagger: 0.1 }, 0.55);

    const tamanho = document.querySelector('.h-titulo .tamanho');
    tamanho?.addEventListener('pointerenter', () => {
        // pulo pelo tamanho da fonte: os "oooo" extras tem altura zero, yPercent nao os moveria
        gsap.fromTo(letrasTamanho, { y: 0 }, {
            y: (i, letra) => -0.12 * parseFloat(getComputedStyle(letra).fontSize),
            duration: 0.22,
            ease: 'power2.out',
            stagger: 0.04,
            yoyo: true,
            repeat: 1,
            overwrite: true
        });
    });

    const hero = document.querySelector('.h-hero');

    if (hero) {
        // O WhatsApp flutuante so aparece depois do hero, para nao cobrir o botao
        ScrollTrigger.create({
            trigger: hero,
            start: 'bottom 70%',
            onEnter: () => document.body.classList.add('mostrar-whats'),
            onLeaveBack: () => document.body.classList.remove('mostrar-whats')
        });
        gsap.to('.h-titulo', {
            yPercent: -14,
            scale: 0.94,
            opacity: 0.2,
            ease: 'none',
            scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true }
        });
    }

    // ---------- Intro: o simbolo se monta e a tela abre ----------
    const intro = document.querySelector('.intro');
    if (html.classList.contains('intro-ativa') && intro) {
        lenis?.stop();
        try {
            sessionStorage.setItem('movcode_intro', '1');
        } catch {
            // sem sessionStorage a intro so aparece de novo na proxima visita
        }
        gsap.timeline({
            onComplete: () => {
                html.classList.remove('intro-ativa');
                intro.remove();
                lenis?.start();
            }
        })
            .from(intro.querySelectorAll('.duo b:last-child'), { yPercent: 160, autoAlpha: 0, duration: 0.6, ease: 'back.out(1.7)', stagger: 0.1 })
            .from(intro.querySelectorAll('.duo b:first-child'), { yPercent: -260, autoAlpha: 0, duration: 0.7, ease: 'bounce.out', stagger: 0.1 }, 0.25)
            .to(intro.querySelector('.duo'), { scale: 1.12, duration: 0.25, ease: 'power2.out' }, '+=0.05')
            .to(intro, { clipPath: 'inset(0% 0% 100% 0%)', duration: 0.9, ease: 'expo.inOut' })
            .add(() => tlHero.play(), '-=0.55');
    } else {
        html.classList.remove('intro-ativa');
        intro?.remove();
        tlHero.play();
    }

    // ---------- A escala: o simbolo cresce e toma a tela ----------
    const palco = document.querySelector('.h-escala-palco');
    if (palco) {
        const duo = palco.querySelector('.h-escala-duo');
        const capitulos = gsap.utils.toArray('.h-escala .h-cap');
        const nomes = capitulos.map((cap) => cap.querySelector('.h-cap-nome'));
        const palavras = capitulos.map((cap) => cap.querySelector('.h-cap-nome-i'));
        const detalhes = capitulos.map((cap) => cap.querySelectorAll('.h-cap-num, .h-cap-linha, .h-cap-link'));
        gsap.set(duo, { xPercent: -50, yPercent: -50, scale: 0.45 });
        gsap.set(nomes, { xPercent: -50, yPercent: -50 });
        // Mesmo efeito dos titulos: a palavra sobe um pouco enquanto sai do desfoque
        const OCULTA_EMBAIXO = { yPercent: 35, opacity: 0, filter: 'blur(14px)' };
        const OCULTA_EM_CIMA = { yPercent: -35, opacity: 0, filter: 'blur(14px)' };
        const NITIDA = { yPercent: 0, opacity: 1, filter: 'blur(0px)' };
        // As palavras seguintes comecam escondidas; os textos pequenos, apagados
        gsap.set(palavras.slice(1), OCULTA_EMBAIXO);
        detalhes.slice(1).forEach((grupo) => gsap.set(grupo, { autoAlpha: 0 }));

        const tl = gsap.timeline({
            defaults: { ease: 'none' },
            scrollTrigger: { trigger: palco, start: 'top top', end: '+=340%', pin: true, scrub: 0.8, anticipatePin: 1 }
        });

        // Troca de palavra: a que sai sobe e se desfaz no desfoque, depois a proxima
        // sobe saindo do desfoque. Nunca as duas ao mesmo tempo. Os textos pequenos
        // trocam com fade suave.
        const sair = (i, em) => tl
            .to(palavras[i], { ...OCULTA_EM_CIMA, duration: 0.24, ease: 'power2.in' }, em)
            .to(detalhes[i], { autoAlpha: 0, duration: 0.18, ease: 'power1.in' }, em);
        const entrar = (i, em) => tl
            .fromTo(palavras[i], OCULTA_EMBAIXO, { ...NITIDA, duration: 0.26, ease: 'power3.out', immediateRender: false }, em)
            .fromTo(detalhes[i], { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.22, ease: 'power1.out', immediateRender: false }, em + 0.06);

        const tamanhos = [1, 1.9, 3.1];
        capitulos.forEach((cap, i) => {
            tl.to(duo, { scale: tamanhos[i], duration: 1 }, i)
                .fromTo(nomes[i], { scale: 0.9 }, { scale: 1.04, duration: 1 }, i);
            if (i > 0) {
                sair(i - 1, i - 0.26);
                entrar(i, i + 0.02);
            }
        });
        sair(capitulos.length - 1, 2.86);
        tl
            .to('.h-escala-fundo', { clipPath: 'circle(150% at 50% 50%)', duration: 0.9, ease: 'power2.in' }, 3)
            .to('.h-escala-progresso i', { scaleX: 1, duration: 3.9 }, 0);
    }

    // ---------- Faixa: acelera e inclina com a velocidade do scroll ----------
    const linhas = gsap.utils.toArray('.h-faixa-linha');
    const letreiros = linhas.map((linha, i) => (
        i % 2
            ? gsap.fromTo(linha, { xPercent: -50 }, { xPercent: 0, duration: 32, ease: 'none', repeat: -1 })
            : gsap.fromTo(linha, { xPercent: 0 }, { xPercent: -50, duration: 32, ease: 'none', repeat: -1 })
    ));
    if (linhas.length) {
        const inclinar = gsap.quickTo(linhas, 'skewX', { duration: 0.4, ease: 'power3' });
        ScrollTrigger.create({
            trigger: '.h-faixa',
            start: 'top bottom',
            end: 'bottom top',
            onUpdate: (self) => {
                const velocidade = gsap.utils.clamp(-10, 10, self.getVelocity() / 200);
                inclinar(-velocidade);
                letreiros.forEach((tween) => gsap.fromTo(tween, { timeScale: 1 + Math.abs(velocidade) }, { timeScale: 1, duration: 1.2, overwrite: true }));
                gsap.delayedCall(0.15, () => inclinar(0));
            }
        });
    }

    // ---------- Conversa: mensagens chegando, com "digitando..." ----------
    const chat = document.querySelector('.chat');
    if (chat) {
        const bolhas = chat.querySelectorAll('.bolha');
        const digitando = document.createElement('div');
        digitando.className = 'digitando';
        digitando.setAttribute('aria-hidden', 'true');
        digitando.innerHTML = '<i></i><i></i><i></i>';
        chat.appendChild(digitando);
        gsap.set(bolhas, { autoAlpha: 0, y: 24, scale: 0.94 });

        const tl = gsap.timeline({ scrollTrigger: { trigger: chat, start: 'top 72%', once: true } });
        bolhas.forEach((bolha) => {
            tl.call(() => {
                digitando.classList.toggle('nossa', bolha.classList.contains('nossa'));
                digitando.style.top = `${bolha.offsetTop}px`;
                digitando.style.display = 'inline-flex';
            })
                .to({}, { duration: 0.6 })
                .call(() => { digitando.style.display = 'none'; })
                .to(bolha, { autoAlpha: 1, y: 0, scale: 1, duration: 0.45, ease: 'back.out(1.8)', transformOrigin: bolha.classList.contains('nossa') ? '100% 100%' : '0% 100%' });
        });
        tl.call(() => digitando.remove());
    }

    // ---------- Servicos: rolagem lateral no desktop ----------
    const midias = gsap.matchMedia();
    midias.add('(min-width: 821px)', () => {
        const pino = document.querySelector('.h-servicos-pin');
        const trilho = document.querySelector('.h-servicos-trilho');
        if (!pino || !trilho) return;
        const distancia = () => Math.max(0, trilho.scrollWidth - window.innerWidth);
        gsap.to(trilho, {
            x: () => -distancia(),
            ease: 'none',
            scrollTrigger: { trigger: pino, start: 'top top', end: () => `+=${distancia()}`, pin: true, scrub: 0.8, invalidateOnRefresh: true }
        });
    });
    midias.add('(max-width: 820px)', () => {
        gsap.utils.toArray('.h-card').forEach((card) => {
            gsap.from(card, { y: 40, autoAlpha: 0, duration: 0.8, ease: 'power3.out', scrollTrigger: { trigger: card, start: 'top 88%' } });
        });
    });

    // ---------- Texto curvo dos cards: desliza devagar pela curva ----------
    // Mede depois das fontes carregarem: o comprimento do texto depende delas
    (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => {
        document.querySelectorAll('.h-card-curva textPath').forEach((caminho, i) => {
            const texto = caminho.parentNode;
            const repeticoes = Math.max(1, Math.round(caminho.textContent.length / (caminho.dataset.repete || caminho.textContent).length));
            const passo = texto.getComputedTextLength() / repeticoes; // comprimento de uma repeticao
            if (!passo) return;
            const inicio = -passo * (0.2 + (i % 3) * 0.25);
            gsap.fromTo(caminho, { attr: { startOffset: inicio } }, {
                attr: { startOffset: inicio - passo },
                duration: passo / 28,
                ease: 'none',
                repeat: -1
            });
        });
    });

    // ---------- Titulos grandes ----------
    gsap.utils.toArray('.h-grande').forEach((titulo) => revelar(titulo, 'palavras'));

    // ---------- Como funciona ----------
    if (document.querySelector('.h-passos')) {
        gsap.fromTo('.h-passos-linha', { scaleX: 0 }, {
            scaleX: 1,
            ease: 'none',
            scrollTrigger: { trigger: '.h-passos', start: 'top 80%', end: 'bottom 60%', scrub: true }
        });
        gsap.from('.h-passo', {
            y: 48,
            autoAlpha: 0,
            duration: 0.9,
            ease: 'power3.out',
            stagger: 0.12,
            scrollTrigger: { trigger: '.h-passos', start: 'top 80%' }
        });
    }

    // ---------- Caso ----------
    const tituloCaso = document.querySelector('.h-caso-titulo');
    if (tituloCaso) {
        revelar(tituloCaso, 'letras', { duration: 1.2 });
        gsap.fromTo('.h-caso-foto', { clipPath: 'inset(16% 14% 16% 14% round 32px)' }, {
            clipPath: 'inset(0% 0% 0% 0% round 32px)',
            ease: 'none',
            scrollTrigger: { trigger: '.h-caso-foto', start: 'top 90%', end: 'top 30%', scrub: true }
        });
        gsap.fromTo('.h-caso-foto img', { scale: 1.08 }, {
            scale: 1,
            ease: 'none',
            scrollTrigger: { trigger: '.h-caso-foto', start: 'top 90%', end: 'top 30%', scrub: true }
        });
        gsap.from('.h-caso-mini, .h-caso-info > *', {
            y: 40,
            autoAlpha: 0,
            duration: 0.9,
            ease: 'power3.out',
            stagger: 0.1,
            scrollTrigger: { trigger: '.h-caso-texto', start: 'top 85%' }
        });
    }

    // ---------- Mais projetos ----------
    gsap.utils.toArray('.h-proj').forEach((proj) => {
        const tl = gsap.timeline({ scrollTrigger: { trigger: proj, start: 'top 88%' } });
        tl.from(proj.querySelector('.h-proj-nome'), {
            yPercent: 40, autoAlpha: 0, filter: 'blur(12px)', duration: 1, ease: 'power3.out', clearProps: 'filter,transform'
        }).from(proj.querySelectorAll('.h-proj-num, .h-proj-desc, .h-proj-tipo, .h-proj-seta'), {
            y: 16, autoAlpha: 0, duration: 0.7, ease: 'power2.out', stagger: 0.06, clearProps: 'transform'
        }, 0.15);
    });

    // ---------- Contato e rodape ----------
    const tituloContato = document.querySelector('.h-contato-titulo');
    if (tituloContato) {
        revelar(tituloContato, 'letras');
        tituloContato.addEventListener('pointerenter', () => {
            gsap.fromTo(tituloContato.querySelectorAll('.l'), { yPercent: 0 }, {
                yPercent: -12, duration: 0.2, ease: 'power2.out', stagger: 0.03, yoyo: true, repeat: 1, overwrite: true
            });
        });
    }
    const gigante = document.querySelector('.rodape-gigante');
    if (gigante) {
        dividir(gigante, 'letras');
        gsap.fromTo(gigante.querySelectorAll('.l, .duo'), ENTRADA, {
            ...CHEGADA,
            duration: 1.2,
            stagger: 0.05,
            scrollTrigger: { trigger: gigante, start: 'top 95%' }
        });
    }

    // ---------- Botoes magneticos e cursor ----------
    if (ponteiroFino) {
        document.querySelectorAll('[data-magnetico]').forEach((el) => {
            const moverX = gsap.quickTo(el, 'x', { duration: 0.6, ease: 'elastic.out(1, 0.4)' });
            const moverY = gsap.quickTo(el, 'y', { duration: 0.6, ease: 'elastic.out(1, 0.4)' });
            el.addEventListener('pointermove', (event) => {
                const caixa = el.getBoundingClientRect();
                moverX((event.clientX - (caixa.left + caixa.width / 2)) * 0.35);
                moverY((event.clientY - (caixa.top + caixa.height / 2)) * 0.35);
            });
            el.addEventListener('pointerleave', () => {
                moverX(0);
                moverY(0);
            });
        });

        const ponto = document.querySelector('.cursor');
        const anel = document.querySelector('.cursor-anel');
        if (ponto && anel) {
            const rotulo = anel.querySelector('span');
            const pontoX = gsap.quickTo(ponto, 'x', { duration: 0.1 });
            const pontoY = gsap.quickTo(ponto, 'y', { duration: 0.1 });
            const anelX = gsap.quickTo(anel, 'x', { duration: 0.45, ease: 'power3' });
            const anelY = gsap.quickTo(anel, 'y', { duration: 0.45, ease: 'power3' });
            window.addEventListener('pointermove', (event) => {
                gsap.to([ponto, anel], { opacity: 1, duration: 0.2, overwrite: 'auto' });
                pontoX(event.clientX);
                pontoY(event.clientY);
                anelX(event.clientX);
                anelY(event.clientY);
            });
            document.addEventListener('pointerover', (event) => {
                const alvo = event.target.closest('a, button, summary, label, [data-cursor]');
                const sobreCampo = event.target.closest('input, textarea');
                anel.classList.toggle('ativo', Boolean(alvo) && !sobreCampo);
                rotulo.textContent = alvo?.dataset.cursor || '';
                anel.classList.toggle('sobre-laranja', Boolean(alvo?.closest('.h-proj-linha')));
                gsap.to(ponto, { opacity: sobreCampo ? 0 : 1, duration: 0.2 });
            });
            document.documentElement.addEventListener('pointerleave', () => gsap.to([ponto, anel], { opacity: 0, duration: 0.2 }));
        }
    }

    // Recalcula as posicoes quando fontes e imagens terminam de carregar
    document.fonts?.ready.then(() => ScrollTrigger.refresh());
    window.addEventListener('load', () => {
        ScrollTrigger.refresh();
        // Chegou com "#secao" (link de outra pagina): rola ate la depois de
        // calcular as secoes travadas e tira o "#" do endereco
        if (window.location.hash) {
            const alvo = document.getElementById(decodeURIComponent(window.location.hash.slice(1)));
            history.replaceState(null, '', window.location.pathname + window.location.search);
            if (alvo) {
                // Espera as fontes e o recalculo das secoes travadas antes de rolar
                const irAteAlvo = () => {
                    ScrollTrigger.refresh();
                    const y = alvo.getBoundingClientRect().top + window.scrollY;
                    if (lenis) {
                        lenis.resize(); // a altura mudou com as secoes travadas
                        lenis.scrollTo(y, { immediate: true, force: true });
                    } else {
                        window.scrollTo(0, y);
                    }
                };
                (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => setTimeout(irAteAlvo, 60));
            }
        }
    });
})();

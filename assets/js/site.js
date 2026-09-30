/* -------------------------------------------------------------------------
   PARA TROCAR O WHATSAPP, MUDE SO A LINHA whatsappNumber ABAIXO.
   Todo link com data-whatsapp no HTML e reescrito a partir daqui.
   Formato: codigo do pais + DDD + numero, sem simbolos. Ex.: 5516991234567
------------------------------------------------------------------------- */
window.MOVCODE_CONFIG = Object.freeze({
    whatsappNumber: '5516000000000',
    whatsappMensagem: 'Olá! Vim pelo site da MovCode e gostaria de conversar sobre um projeto.'
});

// Origem da visita (utm_* / gclid / fbclid), guardada na sessao para o lead
// chegar no WhatsApp dizendo de qual anuncio veio.
window.MOVCODE_ORIGEM = (() => {
    const chaves = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'gclid', 'fbclid'];
    const params = new URLSearchParams(window.location.search);
    const atual = {};

    chaves.forEach((chave) => {
        if (params.get(chave)) {
            atual[chave] = params.get(chave);
        }
    });

    try {
        if (Object.keys(atual).length) {
            sessionStorage.setItem('movcode_origem', JSON.stringify(atual));
            return atual;
        }
        return JSON.parse(sessionStorage.getItem('movcode_origem') || '{}');
    } catch {
        return atual;
    }
})();

function rastrear(evento, dados = {}) {
    if (typeof window.gtag === 'function') {
        window.gtag('event', evento, { ...window.MOVCODE_ORIGEM, ...dados });
    }
}

function linkWhatsapp(texto) {
    const origem = window.MOVCODE_ORIGEM || {};
    const ref = [origem.utm_source, origem.utm_campaign].filter(Boolean).join(' / ')
        || (origem.gclid ? 'google ads' : origem.fbclid ? 'meta ads' : '');
    const mensagem = ref ? `${texto}\n\n(ref: ${ref})` : texto;
    const query = mensagem ? `?text=${encodeURIComponent(mensagem)}` : '';
    return `https://wa.me/${window.MOVCODE_CONFIG.whatsappNumber}${query}`;
}

// Links de WhatsApp
document.querySelectorAll('[data-whatsapp]').forEach((link) => {
    link.href = linkWhatsapp(link.dataset.whatsapp || window.MOVCODE_CONFIG.whatsappMensagem);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
});

// Eventos do GA4. Marque whatsapp_click e generate_lead como conversao.
document.addEventListener('click', (event) => {
    const whatsapp = event.target.closest('[data-whatsapp]');
    const cta = event.target.closest('[data-cta]');

    if (whatsapp) {
        rastrear('whatsapp_click', { local: whatsapp.dataset.cta || 'link', pagina: window.location.pathname });
    } else if (cta) {
        rastrear('cta_click', { cta: cta.dataset.cta, pagina: window.location.pathname });
    }
});

// Botoes que ja escolhem o servico no formulario (ex.: cards de porte)
document.querySelectorAll('[data-servico]').forEach((link) => {
    link.addEventListener('click', () => {
        const opcao = document.querySelector(`.form input[name="servico"][value="${link.dataset.servico}"]`);
        if (opcao) {
            opcao.checked = true;
        }
    });
});

// Cabecalho e menu
(() => {
    const topo = document.querySelector('.topo');
    const botao = document.querySelector('.menu-botao');
    const menu = document.getElementById('menu');

    const marcarRolagem = () => topo?.classList.toggle('rolou', window.scrollY > 8);
    marcarRolagem();
    window.addEventListener('scroll', marcarRolagem, { passive: true });

    if (!botao || !menu) {
        return;
    }

    const fechar = () => {
        document.body.classList.remove('menu-aberto');
        botao.setAttribute('aria-expanded', 'false');
        botao.setAttribute('aria-label', 'Abrir menu');
    };

    botao.addEventListener('click', () => {
        const aberto = document.body.classList.toggle('menu-aberto');
        botao.setAttribute('aria-expanded', String(aberto));
        botao.setAttribute('aria-label', aberto ? 'Fechar menu' : 'Abrir menu');
    });
    menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', fechar));
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') fechar();
    });
    document.addEventListener('click', (event) => {
        if (document.body.classList.contains('menu-aberto') && !menu.contains(event.target) && !botao.contains(event.target)) {
            fechar();
        }
    });
})();

// Formulario de diagnostico: site estatico, entao monta a mensagem e abre o
// WhatsApp ja preenchido.
document.querySelectorAll('[data-lead-form]').forEach((form) => {
    const erro = form.querySelector('.form-erro');

    form.addEventListener('submit', (event) => {
        event.preventDefault();

        const dados = new FormData(form);
        const nome = String(dados.get('nome') || '').trim();
        const empresa = String(dados.get('empresa') || '').trim();
        const servico = String(dados.get('servico') || '').trim();
        const mensagem = String(dados.get('mensagem') || '').trim();

        if (!nome || !servico) {
            if (erro) erro.hidden = false;
            form.querySelector(!nome ? '[name="nome"]' : '[name="servico"]')?.focus();
            return;
        }

        if (erro) erro.hidden = true;

        const linhas = [
            `Olá! Sou ${nome}${empresa ? ` (${empresa})` : ''}.`,
            `Quero um diagnóstico gratuito sobre: ${servico}.`
        ];

        if (mensagem) {
            linhas.push(`Hoje o que mais atrapalha é: ${mensagem}`);
        }

        rastrear('generate_lead', { servico, pagina: window.location.pathname });

        const url = linkWhatsapp(linhas.join('\n'));
        // Sem 'noopener' nas features: com ele window.open sempre devolve null
        // e nao daria para detectar popup bloqueado.
        const janela = window.open(url, '_blank');

        if (janela) {
            janela.opener = null;
        } else {
            window.location.href = url;
        }
    });
});

document.querySelectorAll('[data-ano]').forEach((el) => {
    el.textContent = new Date().getFullYear();
});

// Abertura: escolher o tamanho do negocio troca o texto do que a gente constroi
document.querySelectorAll('[data-escala]').forEach((escala) => {
    const degraus = escala.querySelectorAll('.degrau');
    const texto = escala.querySelector('[data-escala-texto]');

    degraus.forEach((degrau) => {
        degrau.addEventListener('click', () => {
            degraus.forEach((outro) => outro.setAttribute('aria-pressed', String(outro === degrau)));
            if (texto) {
                texto.textContent = degrau.dataset.texto;
            }
            rastrear('hero_porte', { porte: degrau.querySelector('.degrau-nome')?.textContent });
        });
    });
});

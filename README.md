# MovCode

Site institucional da **MovCode**, em [movcode.com.br](https://movcode.com.br).

> Tecnologia do tamanho do seu negócio.

Sites, lojas virtuais, sistemas de gestão e automações sob medida, do mercadinho à indústria. Ribeirão Preto/SP, com atendimento para todo o Brasil.

## Páginas

| URL | Arquivo | Conteúdo |
| --- | --- | --- |
| `/` | `index.html` | Página inicial: soluções, como funciona, projetos, dúvidas e contato |
| `/diagnostico` | `diagnostico.html` | Landing page do diagnóstico gratuito de 30 minutos |
| `/criacao-de-sites` | `criacao-de-sites.html` | Sites e landing pages |
| `/loja-virtual` | `loja-virtual.html` | Lojas virtuais |
| `/sistema-para-mercadinho` | `sistema-para-mercadinho.html` | Sistema de gestão para comércio |
| `/sistema-para-laboratorio` | `sistema-para-laboratorio.html` | ForLabs, controle de qualidade para laboratórios |
| `/sistema-para-barbearia` | `sistema-para-barbearia.html` | ForBarber, site e sistema para barbearias |
| `/politica` | `politica.html` | Política de Privacidade |
| `/termo` | `termo.html` | Termos de Uso |
| — | `404.html` | Página de erro |

`processo.html`, `projetos.html` e `servicos.html` são endereços antigos: só redirecionam para a seção certa da página inicial e não são indexados.

## Estrutura

```
.
├── *.html                 páginas do site (uma por URL)
├── assets/
│   ├── css/
│   │   ├── site.css       estilos compartilhados por todas as páginas
│   │   └── home.css       estilos exclusivos da página inicial
│   ├── js/
│   │   ├── site.js        WhatsApp, formulários, Analytics/Meta Pixel e transições
│   │   ├── home.js        animações da página inicial
│   │   └── vendor/        GSAP, ScrollTrigger e Lenis (versões minificadas)
│   └── images/
│       ├── icons/         favicon e ícones do app
│       ├── logos/         símbolo da marca em SVG
│       ├── og/            imagem de compartilhamento (1200×630)
│       └── projects/      imagens dos projetos
├── site.webmanifest
├── sitemap.xml
├── robots.txt
└── CNAME                  domínio do GitHub Pages
```

Não há build nem dependências: é HTML, CSS e JavaScript puros.

## Rodando localmente

Qualquer servidor estático serve. Por exemplo:

```bash
python3 -m http.server 8000
```

Depois é só abrir [http://localhost:8000](http://localhost:8000). Localmente, os links sem `.html` (como `/diagnostico`) podem não abrir; acesse `/diagnostico.html` nesse caso.

## Configurações rápidas

As configurações ficam no topo de `assets/js/site.js`, em `MOVCODE_CONFIG`:

- **`whatsappNumber`**: número do WhatsApp (código do país + DDD + número, sem símbolos). Todo link com `data-whatsapp` é reescrito a partir dele.
- **`whatsappMensagem`**: mensagem padrão que abre no WhatsApp.
- **`metaPixelId`**: ID do Meta Pixel. Vazio, o pixel fica desligado.

O ID do Google Analytics (GA4) fica no `<head>` de cada página.

## Publicação

O site é publicado pelo **GitHub Pages** a partir da branch `main`, no domínio definido em `CNAME`. Um merge na `main` já coloca a alteração no ar.

Ao criar ou remover uma página, atualize também:

- `sitemap.xml`;
- os links do rodapé (presentes em todas as páginas) e da página `404.html`;
- o `<title>`, a `description`, o `canonical` e as tags `og:*` da própria página.

## Convenções

- Textos em português do Brasil, com títulos em caixa normal (só a primeira letra maiúscula).
- Links internos sem `.html` (`/diagnostico`, não `/diagnostico.html`).
- As perguntas de cada página aparecem também nos dados estruturados (`FAQPage`); ao mudar uma, mude a outra.
- Formatação definida em `.editorconfig`: UTF-8, quebra de linha CRLF e 4 espaços de indentação.

## Licença

[MIT](LICENSE) © MovCode

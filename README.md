# ♠ Royal Felt - Texas Hold'em Poker

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-Real--Time-blueviolet?style=for-the-badge)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-Luxury_Theme-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Um jogo web de Texas Hold'em No-Limit com estética de cassino de luxo e 100% da lógica matemática, regras e inteligência artificial implementadas nativamente em Python.**

[Começar a Jogar](#como-executar) • [Funcionalidades](#funcionalidades) • [Arquitetura](#arquitetura-do-projeto) • [Regras](#hierarquia-de-mãos)

---

## Sobre o Projeto

O **Royal Felt** é uma simulação completa de poker **Texas Hold'em No-Limit** desenvolvida para a web. Todo o estado do jogo, embaralhamento criptográfico, distribuição de cartas, rodadas de apostas (*Pre-flop*, *Flop*, *Turn*, *River*, *Showdown*), cálculo de potes paralelos (*side pots*) e o comportamento de 4 oponentes controlados por IA rodam no backend em **Python**.

O frontend oferece uma experiência de cassino moderna, desenvolvida em Vanilla CSS e JavaScript puro com suporte a **WebSockets** em tempo real, renderização de **cartas reais via CDN** e síntese sonora procedural via **Web Audio API**.

---

## Funcionalidades

### Motor de Jogo em Python

- **Avaliador Completo de 7 Cartas**: Seleciona a melhor combinação de 5 cartas dentre 7 possíveis, resolvendo desempates com precisão matemática por meio de *kickers*.
- **Potes Paralelos e All-in**: Algoritmo robusto que calcula potes principais e múltiplos *side pots* para qualquer quantidade de jogadores em all-in com stacks desiguais.
- **Rotação de Mesa**: Passagem do botão de Dealer (D), Small Blind (SB) e Big Blind (BB) a cada mão.
- **RNG Seguro**: Embaralhamento de baralho de 52 cartas baseado em algoritmo Fisher-Yates com alta entropia.

### Oponentes de IA com Personalidades Únicas

Você enfrenta 4 bots na mesa, cada um com estratégias, tendências de blefe e faixas de abertura distintas:

1. **Viktor "O Rochedo"** (*Tight-Aggressive*): Joga apenas cartas premium, aposta forte quando está à frente e raramente blefa.
2. **Elena "Rainha do Blefe"** (*Loose-Aggressive*): Abre com ampla variedade de mãos, pressiona com semi-blefes e persegue draws agressivamente.
3. **Marco "O Xerife"** (*Calling Station*): Dificilmente desiste de qualquer par ou sequência, paga apostas com frequência e raramente aumenta.
4. **Sofia "A Mestre"** (*GTO Pro / Equilibrada*): Analisa pot odds, textura da mesa, posição e aplica blefes balanceados.

### Cartas Reais em Alta Definição

- Utilização de cartas reais via **Deck of Cards CDN**, com suporte e contingência automática via vetores SVG da **CardsJS**.

### Destaque em Tempo Real na Hierarquia de Mãos

- O modal de regras identifica e ilumina automaticamente a combinação que o jogador possui no momento (com badge animado `★ SUA MÃO`), permitindo acompanhar a evolução da sua mão à medida que as cartas comunitárias são reveladas.

### Sintetizador Sonoro Nativo (Web Audio API)

- Efeitos de áudio procedurais gerados em tempo real pelo navegador (sem download de arquivos externos pesados): deslizamento de cartas, batidas de *check* na mesa, tinir de fichas de cerâmica, descarte (*fold*) e fanfarras de vitória.

---

## Arquitetura do Projeto

```text
Poker/
├── engine/                   # Motor de Poker (100% Python)
│   ├── __init__.py           # Exportação dos módulos principais
│   ├── ai.py                 # Algoritmos de tomada de decisão e personalidades da IA
│   ├── card.py               # Enums de Naipes, Valores, Carta e Deck de 52 cartas
│   ├── evaluator.py          # Avaliador de mãos de 5 a 7 cartas e desempate por kickers
│   ├── game.py               # Máquina de estados da mesa, turnos e regras
│   └── pot.py                # Gestão de potes, side-pots e divisões (split-pot)
│
├── static/                   # Frontend Web
│   ├── css/
│   │   └── style.css         # Design system de cassino, mesa de feltro verde e HUD
│   ├── js/
│   │   ├── api.js            # Cliente WebSocket bidirecional com fallback REST
│   │   ├── app.js            # Controlador da interface, animações e renderizador
│   │   └── audio.js          # Síntese de áudio procedural via Web Audio API
│   └── index.html            # Estrutura da mesa, assentos e modais
│
├── .gitattributes            # Normalização de quebras de linha e estatísticas do GitHub
├── .gitignore                # Padrão de exclusão de artefatos temporários e caches
├── iniciar_jogo.bat          # Script de inicialização em 1 clique (Windows) com suporte a winget
├── requirements.txt          # Dependências do servidor Python (FastAPI, Uvicorn, WebSockets)
├── server.py                 # Servidor assíncrono FastAPI + WebSocket
└── README.md                 # Documentação oficial do projeto
```

---

## Como Executar

### Opção 1: Inicialização em Um Clique (Windows)

Basta dar um duplo clique no arquivo:

```cmd
iniciar_jogo.bat
```

*O script verificará a instalação do Python (com opção de instalação automática via winget se necessário), instalará as dependências, iniciará o servidor e abrirá o navegador automaticamente em `http://127.0.0.1:8000/`.*

---

### Opção 2: Terminal / Linha de Comando (Windows, Linux, macOS)

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/poker-royal-felt.git
   cd poker-royal-felt
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**

   ```bash
   # Linux/macOS:
   python3 -m venv venv
   source venv/bin/activate

   # Windows:
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o servidor:**

   ```bash
   python server.py
   ```

5. **Acesse no seu navegador:**

   [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Hierarquia de Mãos

| Nível | Mão | Descrição | Exemplo |
| :---: | :--- | :--- | :--- |
| **10** | **Royal Flush** | As cinco cartas mais altas do mesmo naipe | `A♠ K♠ Q♠ J♠ 10♠` |
| **9** | **Straight Flush** | Cinco cartas em sequência do mesmo naipe | `9♥ 8♥ 7♥ 6♥ 5♥` |
| **8** | **Quadra** | Quatro cartas do mesmo valor | `K♣ K♦ K♥ K♠ 4♦` |
| **7** | **Full House** | Uma trinca combinada com um par | `J♦ J♠ J♥ 8♣ 8♠` |
| **6** | **Flush** | Cinco cartas quaisquer do mesmo naipe | `A♦ J♦ 9♦ 6♦ 2♦` |
| **5** | **Sequência (Straight)** | Cinco cartas consecutivas de naipes variados | `10♠ 9♦ 8♣ 7♥ 6♠` |
| **4** | **Trinca** | Três cartas do mesmo valor | `Q♠ Q♥ Q♦ 9♣ 3♥` |
| **3** | **Dois Pares** | Dois pares de valores distintos | `10♣ 10♦ 7♠ 7♥ A♣` |
| **2** | **Um Par** | Duas cartas do mesmo valor | `A♥ A♦ K♠ 8♣ 4♦` |
| **1** | **Carta Alta** | Nenhuma combinação; desempate pela maior carta | `A♠ Q♦ 10♣ 7♥ 2♠` |

---

## Tecnologias Utilizadas

- **Backend**: Python 3.10+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), WebSockets nativos.
- **Frontend**: HTML5 Semântico, Vanilla CSS3 (Custom Properties, Glassmorphism, CSS Grid & Flexbox), Vanilla JavaScript (ES6+ Modules).
- **Mídia & SFX**: Deck of Cards API, CardsJS SVG, Web Audio API Synthesizer.
- **Tipografia**: Google Fonts (*Outfit*, *Cinzel*, *JetBrains Mono*).

---

## Licença

Este projeto é distribuído sob a licença **MIT**. Consulte o arquivo de licença para mais informações.

---

## Autor

Desenvolvido por **Caique Novaes**.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-caiquenovaes-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/caiquenovaes/)
[![GitHub](https://img.shields.io/badge/GitHub-caiquenovaes1994-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/caiquenovaes1994)
[![Telegram](https://img.shields.io/badge/Telegram-caiquenovaes1994-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/caiquenovaes1994)
[![Gmail](https://img.shields.io/badge/Gmail-caiquenovaes1994%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:caiquenovaes1994@gmail.com)

---

> *"A sorte distribui as cartas, a estratégia vence o jogo."* ♠

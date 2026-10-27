/**
 * API and WebSocket client for Texas Hold'em.
 * Dual-mode: WebSocket for real-time reactivity with REST fallback.
 */
class PokerClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.onState = null;
        this.onThinking = null;
        this.onStatus = null;
        this.reconnectTimer = null;
        this.useRestFallback = false;
    }

    init({ onState, onThinking, onStatus }) {
        this.onState = onState;
        this.onThinking = onThinking;
        this.onStatus = onStatus;
        this.connectWebSocket();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || '127.0.0.1:8000';
        const wsUrl = `${protocol}//${host}/ws`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.isConnected = true;
                this.useRestFallback = false;
                if (this.onStatus) this.onStatus("online");
                if (this.reconnectTimer) {
                    clearTimeout(this.reconnectTimer);
                    this.reconnectTimer = null;
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'state' && this.onState) {
                        this.onState(msg.data);
                    } else if (msg.type === 'thinking' && this.onThinking) {
                        this.onThinking(msg.player_id, msg.player_name);
                    }
                } catch (e) {
                    console.error("Erro ao processar mensagem WebSocket:", e);
                }
            };

            this.ws.onclose = () => {
                this.isConnected = false;
                if (this.onStatus) this.onStatus("reconnecting");
                this.scheduleReconnect();
            };

            this.ws.onerror = (err) => {
                console.warn("WebSocket falhou, usando modo REST de contingência:", err);
                this.useRestFallback = true;
                this.fetchStateRest();
            };
        } catch (e) {
            this.useRestFallback = true;
            this.fetchStateRest();
        }
    }

    scheduleReconnect() {
        if (!this.reconnectTimer) {
            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                this.connectWebSocket();
            }, 3000);
        }
    }

    async send(payload) {
        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(payload));
            return;
        }

        // REST fallback
        try {
            if (payload.type === 'start_hand') {
                await fetch('/api/start_hand', { method: 'POST' });
            } else if (payload.type === 'action') {
                await fetch('/api/action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: payload.action, amount: payload.amount || 0 })
                });
            } else if (payload.type === 'rebuy') {
                await fetch('/api/rebuy', { method: 'POST' });
            } else if (payload.type === 'reset') {
                await fetch('/api/reset_table', { method: 'POST' });
            }
            await this.fetchStateRest();
        } catch (e) {
            console.error("Falha na chamada REST:", e);
        }
    }

    async fetchStateRest() {
        try {
            const res = await fetch('/api/state');
            if (res.ok) {
                const data = await res.json();
                if (this.onState) this.onState(data);
            }
        } catch (e) {
            console.error("Erro ao buscar estado via REST:", e);
        }
    }

    startHand() {
        this.send({ type: 'start_hand' });
    }

    sendAction(action, amount = 0) {
        this.send({ type: 'action', action, amount });
    }

    rebuy() {
        this.send({ type: 'rebuy' });
    }

    resetTable() {
        this.send({ type: 'reset' });
    }
}

window.pokerClient = new PokerClient();

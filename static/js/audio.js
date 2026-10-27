/**
 * Web Audio API Sound Synthesizer for Poker SFX.
 * Self-contained, zero external asset dependencies, ultra-reliable.
 */
class PokerAudio {
    constructor() {
        this.ctx = null;
        this.muted = false;
        this.volume = 0.5;
        this._initOnInteraction = this._initOnInteraction.bind(this);
        window.addEventListener('click', this._initOnInteraction, { once: true });
        window.addEventListener('keydown', this._initOnInteraction, { once: true });
    }

    _initOnInteraction() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.ctx = new AudioContext();
            }
        }
    }

    ensureContext() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.ctx = new AudioContext();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    toggleMute() {
        this.muted = !this.muted;
        return this.muted;
    }

    // Card Deal swoosh
    playCardDeal() {
        if (this.muted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const filter = this.ctx.createBiquadFilter();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(320, now);
        osc.frequency.exponentialRampToValueAtTime(80, now + 0.12);

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(1200, now);
        filter.frequency.exponentialRampToValueAtTime(300, now + 0.12);

        gain.gain.setValueAtTime(0.18 * this.volume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.12);
    }

    // Casino clay chips clinking sound
    playChipClink() {
        if (this.muted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const frequencies = [2400, 3100, 4200];

        frequencies.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const startTime = now + (idx * 0.025);

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, startTime);
            osc.frequency.exponentialRampToValueAtTime(freq * 0.7, startTime + 0.08);

            gain.gain.setValueAtTime(0.12 * this.volume, startTime);
            gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.08);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(startTime);
            osc.stop(startTime + 0.08);
        });
    }

    // Double table knock for "Check"
    playCheckKnock() {
        if (this.muted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        [0, 0.09].forEach(delay => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const t = now + delay;

            osc.type = 'sine';
            osc.frequency.setValueAtTime(140, t);
            osc.frequency.exponentialRampToValueAtTime(50, t + 0.06);

            gain.gain.setValueAtTime(0.25 * this.volume, t);
            gain.gain.exponentialRampToValueAtTime(0.001, t + 0.06);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(t);
            osc.stop(t + 0.06);
        });
    }

    // Fold swoosh
    playFold() {
        if (this.muted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(180, now);
        osc.frequency.exponentialRampToValueAtTime(70, now + 0.15);

        gain.gain.setValueAtTime(0.15 * this.volume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.15);
    }

    // Gentle alert chime when it's your turn
    playYourTurn() {
        if (this.muted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        [523.25, 659.25].forEach((freq, i) => { // C5, E5
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const t = now + (i * 0.1);

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, t);

            gain.gain.setValueAtTime(0.12 * this.volume, t);
            gain.gain.exponentialRampToValueAtTime(0.001, t + 0.25);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(t);
            osc.stop(t + 0.25);
        });
    }

    // Uplifting victory fanfare (C-E-G-C arpeggio)
    playWin() {
        if (this.muted) return;
        this.ensureContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const startTime = now + (idx * 0.11);
            const dur = (idx === notes.length - 1) ? 0.6 : 0.25;

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, startTime);

            gain.gain.setValueAtTime(0.18 * this.volume, startTime);
            gain.gain.exponentialRampToValueAtTime(0.001, startTime + dur);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(startTime);
            osc.stop(startTime + dur);
        });
    }
}

window.pokerAudio = new PokerAudio();

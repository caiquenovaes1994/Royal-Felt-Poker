/**
 * Royal Felt Poker - Main Web Application Controller.
 * Handles DOM rendering, card CDN images, animations, sound triggers, and game state.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State caches for audio and animation triggers
    let previousState = null;
    let thinkingBotId = null;
    let bannerTimeout = null;

    // DOM Elements
    const elements = {
        blinds: document.getElementById('header-blinds'),
        handCount: document.getElementById('header-hand-count'),
        phase: document.getElementById('header-phase'),
        potTotal: document.getElementById('pot-total-val'),
        commSlots: [
            document.getElementById('comm-slot-0'),
            document.getElementById('comm-slot-1'),
            document.getElementById('comm-slot-2'),
            document.getElementById('comm-slot-3'),
            document.getElementById('comm-slot-4')
        ],
        btnStartHand: document.getElementById('btn-start-hand'),
        playerControls: document.getElementById('player-action-controls'),
        btnFold: document.getElementById('act-btn-fold'),
        btnCheckCall: document.getElementById('act-btn-check-call'),
        checkCallLabel: document.getElementById('check-call-label'),
        checkCallAmount: document.getElementById('check-call-amount'),
        btnRaise: document.getElementById('act-btn-raise'),
        raiseBtnLabel: document.getElementById('raise-btn-label'),
        raiseBtnAmount: document.getElementById('raise-btn-amount'),
        betSlider: document.getElementById('bet-slider'),
        betInput: document.getElementById('bet-input'),
        humanHandHelper: document.getElementById('human-hand-helper'),
        humanHandDesc: document.getElementById('human-hand-desc'),
        logItems: document.getElementById('log-items'),
        connectionStatus: document.getElementById('connection-status'),
        showdownBanner: document.getElementById('showdown-banner'),
        showdownWinner: document.getElementById('showdown-winner-name'),
        showdownHandDesc: document.getElementById('showdown-hand-desc'),
        showdownPayout: document.getElementById('showdown-payout'),
        btnSoundToggle: document.getElementById('btn-sound-toggle'),
        btnRulesModal: document.getElementById('btn-rules-modal'),
        btnStatsModal: document.getElementById('btn-stats-modal'),
        btnResetTable: document.getElementById('btn-reset-table'),
        rulesModal: document.getElementById('rules-modal'),
        statsModal: document.getElementById('stats-modal'),
        statHandsPlayed: document.getElementById('stat-hands-played'),
        statHandsWon: document.getElementById('stat-hands-won'),
        statWinRate: document.getElementById('stat-win-rate'),
        statBiggestPot: document.getElementById('stat-biggest-pot'),
        statProfit: document.getElementById('stat-profit'),
        btnRebuy: document.getElementById('btn-rebuy-action')
    };

    // ================= HELPER: CARD HTML GENERATOR =================
    function createCardElement(card, isTilted = false, tiltDirection = 'left', isWinning = false) {
        const wrap = document.createElement('div');
        wrap.className = 'card-item';
        if (isTilted) {
            wrap.classList.add(tiltDirection === 'left' ? 'tilt-left' : 'tilt-right');
        }
        if (isWinning) {
            wrap.classList.add('winning-card');
        }

        const img = document.createElement('img');
        if (card.face_down) {
            img.src = card.back_url || 'https://deckofcardsapi.com/static/img/back.png';
            img.alt = 'Carta fechada';
        } else {
            img.src = card.image_url;
            img.alt = `${card.rank_label} de ${card.suit_name}`;
            img.onerror = () => {
                if (card.svg_url && img.src !== card.svg_url) {
                    img.src = card.svg_url;
                }
            };
        }
        wrap.appendChild(img);
        return wrap;
    }

    // ================= STATE RENDERER =================
    function renderGameState(state) {
        if (!state) return;

        // Header info
        elements.blinds.textContent = `$${state.small_blind} / $${state.big_blind}`;
        elements.handCount.textContent = `#${state.hand_count}`;
        elements.phase.textContent = state.phase;
        elements.potTotal.textContent = `$${state.total_pot.toLocaleString()}`;

        // Colorize phase
        const phaseColors = {
            'IDLE': '#9ca3af',
            'PREFLOP': '#60a5fa',
            'FLOP': '#34d399',
            'TURN': '#f59e0b',
            'RIVER': '#ec4899',
            'SHOWDOWN': '#f5c85d',
            'HAND_OVER': '#a78bfa'
        };
        elements.phase.style.color = phaseColors[state.phase] || '#ffffff';

        // 1. Render Community Cards
        const winningCardsSet = new Set();
        if (state.winners && state.winners.length > 0) {
            state.winners.forEach(w => {
                if (w.best_cards) {
                    w.best_cards.forEach(c => winningCardsSet.add(c.code));
                }
            });
        }

        // Check if new community cards dealt (trigger sound)
        if (previousState && state.community_cards.length > previousState.community_cards.length) {
            window.pokerAudio.playCardDeal();
        }

        for (let i = 0; i < 5; i++) {
            const slot = elements.commSlots[i];
            slot.innerHTML = '';
            if (i < state.community_cards.length) {
                const card = state.community_cards[i];
                const isWinning = winningCardsSet.has(card.code);
                slot.appendChild(createCardElement(card, false, 'none', isWinning));
            }
        }

        // 2. Render Players
        const numPlayers = state.players.length;
        const dealerIdx = state.dealer_idx;
        const activeIdx = state.current_player_idx;

        // Small Blind and Big Blind calculation for badges
        const sbIdx = dealerIdx >= 0 ? (dealerIdx + 1) % numPlayers : -1;
        const bbIdx = dealerIdx >= 0 ? (dealerIdx + 2) % numPlayers : -1;

        state.players.forEach((player, pIdx) => {
            const seatEl = document.getElementById(`seat-${player.id}`);
            if (!seatEl) return;

            // Turn Highlight & Thinking
            const isTurn = (pIdx === activeIdx && state.phase !== 'HAND_OVER' && state.phase !== 'IDLE');
            seatEl.classList.toggle('active-turn', isTurn);
            seatEl.classList.toggle('thinking', isTurn && !player.is_human);
            seatEl.classList.toggle('folded', player.folded);

            // Turn sound for human
            if (isTurn && player.is_human && (!previousState || previousState.current_player_idx !== pIdx)) {
                window.pokerAudio.playYourTurn();
            }

            // Chips
            const chipsEl = document.getElementById(`chips-${player.id}`);
            if (chipsEl) chipsEl.textContent = `$${player.chips.toLocaleString()}`;

            // Bet on table
            const betEl = document.getElementById(`bet-${player.id}`);
            if (betEl) {
                if (player.current_bet > 0) {
                    betEl.style.display = 'flex';
                    betEl.innerHTML = `🪙 $${player.current_bet}`;
                } else {
                    betEl.style.display = 'none';
                }
            }

            // Action Status Pill
            const actionPill = document.getElementById(`action-pill-${player.id}`);
            if (actionPill) {
                if (player.last_action) {
                    actionPill.style.display = 'block';
                    actionPill.textContent = player.last_action;
                    actionPill.className = 'action-status-pill';
                    const actLower = player.last_action.toLowerCase();
                    if (actLower.includes('fold')) actionPill.classList.add('fold');
                    else if (actLower.includes('raise') || actLower.includes('apostar')) actionPill.classList.add('raise');
                    else if (actLower.includes('all-in')) actionPill.classList.add('allin');
                    else if (actLower.includes('check')) actionPill.classList.add('check');
                    else if (actLower.includes('call')) actionPill.classList.add('call');
                } else {
                    actionPill.style.display = 'none';
                }
            }

            // Role Badge (D, SB, BB)
            const roleEl = document.getElementById(`role-${player.id}`);
            if (roleEl) {
                if (pIdx === dealerIdx) {
                    roleEl.style.display = 'flex';
                    roleEl.className = 'role-badge dealer';
                    roleEl.textContent = 'D';
                } else if (pIdx === sbIdx) {
                    roleEl.style.display = 'flex';
                    roleEl.className = 'role-badge sb';
                    roleEl.textContent = 'SB';
                } else if (pIdx === bbIdx) {
                    roleEl.style.display = 'flex';
                    roleEl.className = 'role-badge bb';
                    roleEl.textContent = 'BB';
                } else {
                    roleEl.style.display = 'none';
                }
            }

            // Hole Cards
            const cardsContainer = document.getElementById(`cards-${player.id}`);
            if (cardsContainer) {
                cardsContainer.innerHTML = '';
                if (player.cards && player.cards.length > 0) {
                    player.cards.forEach((card, cIdx) => {
                        const isWinning = card.code && winningCardsSet.has(card.code);
                        const tilt = cIdx === 0 ? 'left' : 'right';
                        cardsContainer.appendChild(createCardElement(card, true, tilt, isWinning));
                    });
                }
            }
        });

        // 3. Human Hand Evaluator Helper
        const human = state.players.find(p => p.is_human);
        if (human && human.hand_rank && !human.folded && state.phase !== 'IDLE') {
            elements.humanHandHelper.style.display = 'flex';
            elements.humanHandDesc.textContent = human.hand_rank.description;
        } else {
            elements.humanHandHelper.style.display = 'none';
        }

        // 4. Action Dock Controls
        const isHumanTurn = (state.current_player_idx === 0 && state.phase !== 'HAND_OVER' && state.phase !== 'IDLE');
        const ha = state.human_actions || {};

        if (state.phase === 'HAND_OVER' || state.phase === 'IDLE') {
            elements.btnStartHand.style.display = 'block';
            elements.playerControls.style.opacity = '0.4';
            elements.btnFold.disabled = true;
            elements.btnCheckCall.disabled = true;
            elements.btnRaise.disabled = true;
            elements.betSlider.disabled = true;
            elements.betInput.disabled = true;
        } else {
            elements.btnStartHand.style.display = 'none';
            elements.playerControls.style.opacity = isHumanTurn ? '1' : '0.4';

            // FOLD
            elements.btnFold.disabled = !isHumanTurn || !ha.can_fold;

            // CHECK or CALL
            elements.btnCheckCall.disabled = !isHumanTurn || (!ha.can_check && !ha.can_call);
            if (ha.can_check) {
                elements.checkCallLabel.textContent = 'CHECK';
                elements.checkCallAmount.textContent = 'Passar';
            } else if (ha.can_call) {
                elements.checkCallLabel.textContent = 'CALL';
                elements.checkCallAmount.textContent = `$${ha.call_amount}`;
            }

            // RAISE / BET
            elements.btnRaise.disabled = !isHumanTurn || !ha.can_raise;
            elements.betSlider.disabled = !isHumanTurn || !ha.can_raise;
            elements.betInput.disabled = !isHumanTurn || !ha.can_raise;

            if (ha.can_raise) {
                const minR = ha.min_raise || state.big_blind;
                const maxR = ha.max_raise || (human ? human.chips + human.current_bet : 1000);

                elements.betSlider.min = minR;
                elements.betSlider.max = maxR;
                elements.betInput.min = minR;
                elements.betInput.max = maxR;

                let curVal = parseInt(elements.betInput.value, 10);
                if (isNaN(curVal) || curVal < minR || curVal > maxR) {
                    curVal = minR;
                    elements.betSlider.value = curVal;
                    elements.betInput.value = curVal;
                }

                updateRaiseButtonText(curVal, state.current_bet);
            }
        }

        // 5. Showdown Banner Overlay
        if ((state.phase === 'SHOWDOWN' || state.phase === 'HAND_OVER') && state.winners && state.winners.length > 0) {
            const w = state.winners[0];
            elements.showdownWinner.textContent = `🏆 ${w.player_name} Venceu!`;
            elements.showdownHandDesc.textContent = w.hand_desc || w.reason;
            elements.showdownPayout.textContent = `+$${w.amount.toLocaleString()}`;
            elements.showdownBanner.classList.add('show');

            if (w.player_id === 'player_0') {
                window.pokerAudio.playWin();
            }

            if (bannerTimeout) clearTimeout(bannerTimeout);
            bannerTimeout = setTimeout(() => {
                elements.showdownBanner.classList.remove('show');
            }, 6000);
        } else {
            elements.showdownBanner.classList.remove('show');
        }

        // 6. Action History Log
        renderActionHistory(state.action_history);

        // 7. Update Stats in modal
        if (state.stats) {
            elements.statHandsPlayed.textContent = state.stats.hands_played;
            elements.statHandsWon.textContent = state.stats.hands_won;
            const winRate = state.stats.hands_played > 0 
                ? ((state.stats.hands_won / state.stats.hands_played) * 100).toFixed(1) 
                : '0.0';
            elements.statWinRate.textContent = `${winRate}%`;
            elements.statBiggestPot.textContent = `$${state.stats.biggest_pot.toLocaleString()}`;
            elements.statProfit.textContent = `$${state.stats.total_profit.toLocaleString()}`;
        }

        // 8. Update Hand Hierarchy Modal Highlighting
        updateHierarchyModalHighlight(state);

        // Audio cues on state changes
        triggerActionSounds(previousState, state);
        previousState = state;
    }

    // ================= HIERARCHY MODAL HIGHLIGHT =================
    function updateHierarchyModalHighlight(state) {
        if (!state) return;
        const human = state.players ? state.players.find(p => p.is_human) : null;
        const modalDesc = document.getElementById('modal-current-hand-text');
        const rows = document.querySelectorAll('#rules-modal .hand-rank-row');

        if (human && human.hand_rank && !human.folded && state.phase !== 'IDLE' && human.cards && human.cards.length > 0) {
            const cat = human.hand_rank.category; // integer 1 to 10
            const desc = human.hand_rank.description;

            if (modalDesc) {
                modalDesc.textContent = desc;
                modalDesc.style.color = '#f5c85d';
            }

            rows.forEach(row => {
                const rowCat = parseInt(row.getAttribute('data-category'), 10);
                const nameWrap = row.querySelector('.name-wrap');
                let badge = row.querySelector('.hand-current-badge');

                if (rowCat === cat) {
                    row.classList.add('active-current-hand');
                    if (!badge && nameWrap) {
                        badge = document.createElement('span');
                        badge.className = 'hand-current-badge';
                        badge.textContent = '★ SUA MÃO';
                        nameWrap.appendChild(badge);
                    }
                } else {
                    row.classList.remove('active-current-hand');
                    if (badge) badge.remove();
                }
            });
        } else {
            if (modalDesc) {
                if (human && human.folded) {
                    modalDesc.textContent = "Você deu Fold nesta rodada.";
                    modalDesc.style.color = '#ef4444';
                } else {
                    modalDesc.textContent = "Aguardando início da mão...";
                    modalDesc.style.color = '#9ca3af';
                }
            }
            rows.forEach(row => {
                row.classList.remove('active-current-hand');
                const badge = row.querySelector('.hand-current-badge');
                if (badge) badge.remove();
            });
        }
    }

    // ================= SOUND EFFECT TRIGGERS =================
    function triggerActionSounds(prev, curr) {
        if (!prev) return;

        // Check if any player bet or called
        let betChanged = false;
        curr.players.forEach((p, idx) => {
            const prevP = prev.players[idx];
            if (prevP && p.current_bet > prevP.current_bet) {
                betChanged = true;
            }
            if (prevP && p.folded && !prevP.folded) {
                window.pokerAudio.playFold();
            }
            if (prevP && p.last_action && p.last_action.toLowerCase().includes('check') && p.last_action !== prevP.last_action) {
                window.pokerAudio.playCheckKnock();
            }
        });

        if (betChanged) {
            window.pokerAudio.playChipClink();
        }
    }

    function updateRaiseButtonText(amount, currentBet) {
        const isRaise = currentBet > 0;
        elements.raiseBtnLabel.textContent = isRaise ? 'AUMENTAR' : 'APOSTAR';
        elements.raiseBtnAmount.textContent = `$${amount}`;
    }

    // ================= ACTION HISTORY RENDERER =================
    function renderActionHistory(history) {
        if (!history) return;
        elements.logItems.innerHTML = '';
        history.forEach(item => {
            const div = document.createElement('div');
            div.className = `log-entry ${item.type || 'info'}`;

            const timeSpan = document.createElement('span');
            timeSpan.className = 'time';
            timeSpan.textContent = `[${item.time}]`;

            const msgSpan = document.createElement('span');
            msgSpan.textContent = item.message;

            div.appendChild(timeSpan);
            div.appendChild(msgSpan);
            elements.logItems.appendChild(div);
        });
        elements.logItems.scrollTop = elements.logItems.scrollHeight;
    }

    // ================= EVENT HANDLERS =================

    // Bet slider and input synchronization
    elements.betSlider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value, 10);
        elements.betInput.value = val;
        updateRaiseButtonText(val, previousState ? previousState.current_bet : 0);
    });

    elements.betInput.addEventListener('change', (e) => {
        let val = parseInt(e.target.value, 10);
        const min = parseInt(elements.betSlider.min, 10) || 20;
        const max = parseInt(elements.betSlider.max, 10) || 1000;
        if (isNaN(val) || val < min) val = min;
        if (val > max) val = max;
        elements.betInput.value = val;
        elements.betSlider.value = val;
        updateRaiseButtonText(val, previousState ? previousState.current_bet : 0);
    });

    // Preset buttons
    document.querySelectorAll('.preset-chip-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!previousState || !previousState.human_actions) return;
            const ha = previousState.human_actions;
            const minR = ha.min_raise || 20;
            const maxR = ha.max_raise || 1000;
            const pot = ha.pot_size || 0;
            const bb = previousState.big_blind || 20;
            const curBet = previousState.current_bet || 0;
            const type = btn.getAttribute('data-preset');

            let target = minR;
            if (type === 'min') {
                target = minR;
            } else if (type === '2.5bb') {
                target = curBet + Math.round(bb * 2.5);
            } else if (type === '3bb') {
                target = curBet + (bb * 3);
            } else if (type === 'half_pot') {
                target = curBet + Math.max(minR, Math.round(pot * 0.5));
            } else if (type === 'pot') {
                target = curBet + Math.max(minR, pot);
            } else if (type === 'allin') {
                target = maxR;
            }

            target = Math.max(minR, Math.min(maxR, target));
            elements.betSlider.value = target;
            elements.betInput.value = target;
            updateRaiseButtonText(target, curBet);
        });
    });

    // FOLD BUTTON
    elements.btnFold.addEventListener('click', () => {
        window.pokerAudio.playFold();
        window.pokerClient.sendAction('fold');
    });

    // CHECK / CALL BUTTON
    elements.btnCheckCall.addEventListener('click', () => {
        if (!previousState || !previousState.human_actions) return;
        const ha = previousState.human_actions;
        if (ha.can_check) {
            window.pokerAudio.playCheckKnock();
            window.pokerClient.sendAction('check');
        } else if (ha.can_call) {
            window.pokerAudio.playChipClink();
            window.pokerClient.sendAction('call');
        }
    });

    // RAISE BUTTON
    elements.btnRaise.addEventListener('click', () => {
        const amt = parseInt(elements.betInput.value, 10);
        window.pokerAudio.playChipClink();
        window.pokerClient.sendAction('raise', amt);
    });

    // START HAND BUTTON
    elements.btnStartHand.addEventListener('click', () => {
        window.pokerAudio.playCardDeal();
        window.pokerClient.startHand();
    });

    // MUTE / UNMUTE
    elements.btnSoundToggle.addEventListener('click', () => {
        const isMuted = window.pokerAudio.toggleMute();
        elements.btnSoundToggle.textContent = isMuted ? '🔇' : '🔊';
    });

    // MODALS
    function openRulesModal() {
        elements.rulesModal.classList.add('active');
        updateHierarchyModalHighlight(previousState);
        setTimeout(() => {
            const activeRow = document.querySelector('#rules-modal .hand-rank-row.active-current-hand');
            if (activeRow) {
                activeRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 150);
    }

    elements.btnRulesModal.addEventListener('click', openRulesModal);
    elements.humanHandHelper.addEventListener('click', openRulesModal);

    elements.btnStatsModal.addEventListener('click', () => {
        elements.statsModal.classList.add('active');
    });

    document.querySelectorAll('[data-close-modal]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-close-modal');
            const target = document.getElementById(modalId);
            if (target) target.classList.remove('active');
        });
    });

    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-backdrop')) {
            e.target.classList.remove('active');
        }
    });

    // REBUY
    elements.btnRebuy.addEventListener('click', () => {
        window.pokerClient.rebuy();
        elements.statsModal.classList.remove('active');
    });

    // RESET TABLE
    elements.btnResetTable.addEventListener('click', () => {
        if (confirm("Deseja realmente reiniciar a mesa e zerar todas as fichas?")) {
            window.pokerClient.resetTable();
        }
    });

    // ================= INITIALIZE NETWORKING =================
    window.pokerClient.init({
        onState: (state) => {
            renderGameState(state);
        },
        onThinking: (botId, botName) => {
            const seat = document.getElementById(`seat-${botId}`);
            if (seat) seat.classList.add('thinking');
        },
        onStatus: (status) => {
            if (status === 'online') {
                elements.connectionStatus.textContent = '● Ao Vivo';
                elements.connectionStatus.style.color = '#34d399';
            } else {
                elements.connectionStatus.textContent = '○ Reconectando...';
                elements.connectionStatus.style.color = '#f59e0b';
            }
        }
    });

    // Auto-start initial hand if table is idle
    setTimeout(() => {
        if (previousState && previousState.phase === 'IDLE') {
            window.pokerClient.startHand();
        }
    }, 800);
});

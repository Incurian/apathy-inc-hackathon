/**
 * DEFCON Spectator - Main Application
 * Coordinates API polling, map rendering, and UI panels
 */

const API_BASE = '/api';
const POLL_INTERVAL = 500;

class SpectatorApp {
    constructor() {
        this.state = null;
        this.polling = false;
        this.pollTimer = null;
        
        this.initElements();
        this.initPanels();
        this.initMap();
        this.bindControls();
        this.startPolling();
    }

    initElements() {
        this.mapSvg = document.getElementById('mapSvg');
        this.scoreboardEl = document.getElementById('scoreboard');
        this.eventsListEl = document.getElementById('eventsList');
        this.inspectorContentEl = document.getElementById('inspectorContent');
        this.inspectorCloseEl = document.getElementById('inspectorClose');
        this.leadingFactionEl = document.getElementById('leadingFaction');
        
        this.btnStart = document.getElementById('btnStart');
        this.btnPause = document.getElementById('btnPause');
        this.btnResume = document.getElementById('btnResume');
        this.btnReset = document.getElementById('btnReset');
    }

    initPanels() {
        this.scoreboard = new ScoreboardPanel(this.scoreboardEl, (faction) => this.onFactionSelect(faction));
        this.eventLog = new EventLogPanel(this.eventsListEl);
        this.inspector = new InspectorPanel(this.inspectorContentEl);
        
        this.inspectorCloseEl.addEventListener('click', () => this.closeInspector());
    }

    initMap() {
        this.map = new MapRenderer(this.mapSvg);
        window.onEntitySelect = (entity) => this.onEntitySelect(entity);
    }

    bindControls() {
        this.btnStart.addEventListener('click', () => this.apiCall('/start', 'POST'));
        this.btnPause.addEventListener('click', () => this.apiCall('/pause', 'POST'));
        this.btnResume.addEventListener('click', () => this.apiCall('/resume', 'POST'));
        this.btnReset.addEventListener('click', () => this.apiCall('/reset', 'POST'));
    }

    async apiCall(endpoint, method = 'GET', body = null) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: method !== 'GET' ? JSON.stringify(body ?? {}) : null
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.updateState(data);
            return data;
        } catch (error) {
            console.error(`API call failed: ${endpoint}`, error);
        }
    }

    startPolling() {
        this.polling = true;
        this.poll();
    }

    stopPolling() {
        this.polling = false;
        if (this.pollTimer) {
            clearTimeout(this.pollTimer);
            this.pollTimer = null;
        }
    }

    async poll() {
        if (!this.polling) return;
        
        try {
            const response = await fetch(`${API_BASE}/state`);
            if (response.ok) {
                const data = await response.json();
                this.updateState(data);
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
        
        this.pollTimer = setTimeout(() => this.poll(), POLL_INTERVAL);
    }

    updateState(newState) {
        const wasRunning = this.state?.match?.lifecycleState === 'running';
        const isRunning = newState.match?.lifecycleState === 'running';
        
        this.state = newState;
        
        this.updateHeader(newState.match);
        this.updateMap(newState);
        this.updatePanels(newState);
        this.updateControls(newState.match.lifecycleState);
        
        if (!wasRunning && isRunning) {
            console.log('Match started');
        } else if (wasRunning && !isRunning) {
            console.log('Match ended/paused');
        }
    }

    updateHeader(match) {
        this.map.updateMatchInfo(match);
        
        const leading = this.state?.summary?.leadingFaction;
        const faction = this.state?.factions?.find(f => f.id === leading);
        this.leadingFactionEl.textContent = faction ? faction.name : '--';
        this.leadingFactionEl.style.color = faction?.color || '';
    }

    updateMap(state) {
        this.map.render(state);
    }

    updatePanels(state) {
        this.scoreboard.render(state.factions);
        this.eventLog.render(state.recentEvents);
    }

    updateControls(lifecycleState) {
        const isRunning = lifecycleState === 'running';
        const isPaused = lifecycleState === 'paused';
        const isIdle = lifecycleState === 'idle';
        const isFinished = lifecycleState === 'finished';
        
        this.btnStart.disabled = !isIdle && !isFinished;
        this.btnPause.disabled = !isRunning;
        this.btnResume.disabled = !isPaused;
        this.btnReset.disabled = false;
    }

    onFactionSelect(faction) {
        this.inspector.inspectFaction(faction, this.state.nodes, this.state.missiles);
        this.openInspector();
    }

    onEntitySelect(entity) {
        if (!entity || !this.state) {
            this.inspector.showEmpty();
            return;
        }

        const factionMap = new Map(this.state.factions.map(f => [f.id, f]));
        const nodeMap = new Map(this.state.nodes.map(n => [n.id, n]));

        switch (entity.type) {
            case 'node':
                const node = nodeMap.get(entity.id);
                const faction = factionMap.get(node?.owner);
                this.inspector.inspectNode(node, faction, this.state.missiles);
                this.openInspector();
                break;
            case 'missile':
                const missile = this.state.missiles.find(m => m.id === entity.id);
                const mFaction = factionMap.get(missile?.owner);
                const source = nodeMap.get(missile?.source);
                const target = nodeMap.get(missile?.target);
                this.inspector.inspectMissile(missile, mFaction, source, target);
                this.openInspector();
                break;
            default:
                this.inspector.showEmpty();
        }
    }

    openInspector() {
        document.getElementById('inspectorPanel').classList.add('open');
    }

    closeInspector() {
        document.getElementById('inspectorPanel').classList.remove('open');
        this.map.selectEntity(null);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new SpectatorApp();
});
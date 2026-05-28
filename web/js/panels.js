/**
 * UI Panels - Scoreboard, Event Log, and Inspector
 */

class ScoreboardPanel {
    constructor(container, onSelectFaction) {
        this.container = container;
        this.onSelectFaction = onSelectFaction;
        this.selectedFaction = null;
    }

    render(factions) {
        this.container.innerHTML = factions.map(faction => `
            <div class="faction-row ${this.selectedFaction === faction.id ? 'selected' : ''}" 
                 data-faction="${faction.id}" 
                 style="border-left: 3px solid ${faction.color}">
                <div class="faction-color" style="background: ${faction.color}"></div>
                <div class="faction-info">
                    <div class="faction-name">${faction.name}</div>
                    <div class="faction-metrics">
                        <span>Pop: <strong>${faction.population}</strong></span>
                        <span>Score: <strong>${faction.score}</strong></span>
                    </div>
                </div>
                <span class="faction-status status-${faction.status}">${faction.status}</span>
            </div>
        `).join('');

        this.container.querySelectorAll('.faction-row').forEach(row => {
            row.addEventListener('click', () => {
                const factionId = row.dataset.faction;
                this.selectFaction(factionId);
                const faction = factions.find(f => f.id === factionId);
                if (this.onSelectFaction) this.onSelectFaction(faction);
            });
        });
    }

    selectFaction(factionId) {
        this.selectedFaction = factionId;
        this.container.querySelectorAll('.faction-row').forEach(row => {
            row.classList.toggle('selected', row.dataset.faction === factionId);
        });
    }
}

class EventLogPanel {
    constructor(container) {
        this.container = container;
        this.maxEvents = 50;
    }

    render(events) {
        const recentEvents = events.slice(-this.maxEvents).reverse();
        
        this.container.innerHTML = recentEvents.map(event => `
            <div class="event-entry">
                <span class="event-time">${this.formatEventTime(event.time)}</span>
                <span class="event-type event-type-${event.type}">${this.formatEventType(event.type)}</span>
                <span class="event-details">${this.formatEventDetails(event)}</span>
            </div>
        `).join('');
    }

    formatEventTime(timeStr) {
        try {
            const date = new Date(timeStr);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch {
            return '--:--:--';
        }
    }

    formatEventType(type) {
        return type.replace('_', ' ').toUpperCase();
    }

    formatEventDetails(event) {
        switch (event.type) {
            case 'launch':
                return `${event.faction?.toUpperCase()} launched from ${event.source} → ${event.target}`;
            case 'impact':
                return `${event.faction?.toUpperCase()} missile hit ${event.target} (${event.damage} dmg)${event.destroyed ? ' - DESTROYED' : ''}`;
            case 'destruction':
                return `${event.faction?.toUpperCase()} ${event.targetType} ${event.target} destroyed`;
            case 'hold':
                return `${event.faction?.toUpperCase()} holds`;
            case 'invalid_action':
                return `${event.faction?.toUpperCase()} invalid action: ${event.reason}`;
            case 'match_start':
                return `Match started: ${event.matchId}`;
            case 'match_end':
                return `Match ended - ${event.winner?.toUpperCase()} wins!`;
            case 'match_paused':
                return 'Match paused';
            case 'faction_eliminated':
                return `${event.faction?.toUpperCase()} eliminated`;
            case 'faction_crippled':
                return `${event.faction?.toUpperCase()} crippled (no launch capability)`;
            default:
                return JSON.stringify(event);
        }
    }
}

class InspectorPanel {
    constructor(container) {
        this.container = container;
        this.currentEntity = null;
        this.entityType = null;
    }

    showEmpty() {
        this.container.innerHTML = `
            <p class="inspector-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; margin-bottom: 1rem; opacity: 0.5;">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 16v-4M12 8h.01"/>
                </svg>
                Click a faction, city, silo, or missile to inspect
            </p>
        `;
        this.currentEntity = null;
    }

    inspectFaction(faction, nodes, missiles) {
        this.currentEntity = faction;
        this.entityType = 'faction';
        
        const factionNodes = nodes.filter(n => faction.sites?.includes(n.id));
        const cities = factionNodes.filter(n => n.type === 'city');
        const silos = factionNodes.filter(n => n.type === 'silo');
        const activeMissiles = missiles.filter(m => m.owner === faction.id && m.status === 'flying');
        
        this.container.innerHTML = `
            <div class="inspector-section">
                <div class="inspector-section-title">FACTION STATUS</div>
                <div class="inspector-row"><span class="inspector-label">Name</span><span class="inspector-value" style="color: ${faction.color}">${faction.name}</span></div>
                <div class="inspector-row"><span class="inspector-label">Status</span><span class="inspector-value ${this.getStatusClass(faction.status)}">${faction.status.toUpperCase()}</span></div>
                <div class="inspector-row"><span class="inspector-label">Control Mode</span><span class="inspector-value">${faction.controlMode.toUpperCase()}</span></div>
            </div>
            <div class="inspector-section">
                <div class="inspector-section-title">SCORING</div>
                <div class="inspector-row"><span class="inspector-label">Population</span><span class="inspector-value">${faction.population}</span></div>
                <div class="inspector-row"><span class="inspector-label">Score</span><span class="inspector-value good">${faction.score}</span></div>
            </div>
            <div class="inspector-section">
                <div class="inspector-section-title">ASSETS</div>
                <div class="inspector-row"><span class="inspector-label">Cities</span><span class="inspector-value">${cities.filter(c => c.status !== 'destroyed').length} / ${cities.length}</span></div>
                <div class="inspector-row"><span class="inspector-label">Silos</span><span class="inspector-value">${silos.filter(s => s.status !== 'destroyed').length} / ${silos.length}</span></div>
                <div class="inspector-row"><span class="inspector-label">Missiles in Flight</span><span class="inspector-value">${activeMissiles.length}</span></div>
                <div class="inspector-row"><span class="inspector-label">Total Ammo</span><span class="inspector-value">${silos.reduce((sum, s) => sum + (s.ammo || 0), 0)}</span></div>
            </div>
            <div class="inspector-section">
                <div class="inspector-section-title">LAST ACTION</div>
                <div class="inspector-row"><span class="inspector-label">Type</span><span class="inspector-value">${faction.lastAction?.type?.toUpperCase() || 'NONE'}</span></div>
                ${faction.lastAction?.type === 'launch' ? `
                <div class="inspector-row"><span class="inspector-label">From</span><span class="inspector-value">${faction.lastAction.from}</span></div>
                <div class="inspector-row"><span class="inspector-label">Target</span><span class="inspector-value">${faction.lastAction.target}</span></div>
                ` : ''}
            </div>
            ${faction.invalidActionCount > 0 ? `
            <div class="inspector-section">
                <div class="inspector-section-title">WARNINGS</div>
                <div class="inspector-row"><span class="inspector-label">Invalid Actions</span><span class="inspector-value danger">${faction.invalidActionCount}</span></div>
            </div>
            ` : ''}
        `;
    }

    inspectNode(node, faction, missiles) {
        this.currentEntity = node;
        this.entityType = 'node';
        
        const incomingMissiles = missiles.filter(m => m.target === node.id && m.status === 'flying');
        
        this.container.innerHTML = `
            <div class="inspector-section">
                <div class="inspector-section-title">${node.type.toUpperCase()} STATUS</div>
                <div class="inspector-row"><span class="inspector-label">Name</span><span class="inspector-value" style="color: ${faction?.color}">${node.name}</span></div>
                <div class="inspector-row"><span class="inspector-label">Owner</span><span class="inspector-value" style="color: ${faction?.color}">${faction?.name || node.owner}</span></div>
                <div class="inspector-row"><span class="inspector-label">Status</span><span class="inspector-value ${this.getStatusClass(node.status)}">${node.status.toUpperCase()}</span></div>
                <div class="inspector-row"><span class="inspector-label">HP</span><span class="inspector-value ${node.hp < 30 ? 'danger' : node.hp < 70 ? 'warning' : ''}">${node.hp}/100</span></div>
            </div>
            ${node.type === 'city' ? `
            <div class="inspector-section">
                <div class="inspector-section-title">POPULATION</div>
                <div class="inspector-row"><span class="inspector-label">Current</span><span class="inspector-value">${node.population}</span></div>
                <div class="inspector-row"><span class="inspector-label">Value</span><span class="inspector-value good">${node.population} pts</span></div>
            </div>
            ` : ''}
            ${node.type === 'silo' ? `
            <div class="inspector-section">
                <div class="inspector-section-title">SILO STATUS</div>
                <div class="inspector-row"><span class="inspector-label">Ammo</span><span class="inspector-value ${node.ammo === 0 ? 'danger' : node.ammo < 3 ? 'warning' : ''}">${node.ammo}/6</span></div>
                <div class="inspector-row"><span class="inspector-label">Cooldown</span><span class="inspector-value">${node.cooldown > 0 ? `${node.cooldown} ticks` : 'Ready'}</span></div>
                <div class="inspector-row"><span class="inspector-label">Last Launch</span><span class="inspector-value">${node.lastLaunchTick ? `Tick ${node.lastLaunchTick}` : 'Never'}</span></div>
            </div>
            ` : ''}
            ${incomingMissiles.length > 0 ? `
            <div class="inspector-section">
                <div class="inspector-section-title">INCOMING THREATS</div>
                ${incomingMissiles.map(m => `
                <div class="inspector-row"><span class="inspector-label">Missile</span><span class="inspector-value warning">${m.id} (${Math.round((m.impactTick - m.currentTick) * 0.25)}s)</span></div>
                `).join('')}
            </div>
            ` : ''}
        `;
    }

    inspectMissile(missile, faction, sourceNode, targetNode) {
        this.currentEntity = missile;
        this.entityType = 'missile';
        
        const eta = Math.max(0, (missile.impactTick - missile.currentTick) * 0.25);
        
        this.container.innerHTML = `
            <div class="inspector-section">
                <div class="inspector-section-title">MISSILE STATUS</div>
                <div class="inspector-row"><span class="inspector-label">ID</span><span class="inspector-value">${missile.id}</span></div>
                <div class="inspector-row"><span class="inspector-label">Owner</span><span class="inspector-value" style="color: ${faction?.color}">${faction?.name || missile.owner}</span></div>
                <div class="inspector-row"><span class="inspector-label">Status</span><span class="inspector-value">${missile.status.toUpperCase()}</span></div>
                <div class="inspector-row"><span class="inspector-label">Progress</span><span class="inspector-value">${Math.round(missile.progress * 100)}%</span></div>
                <div class="inspector-row"><span class="inspector-label">ETA</span><span class="inspector-value">${eta.toFixed(1)}s</span></div>
            </div>
            <div class="inspector-section">
                <div class="inspector-section-title">TRAJECTORY</div>
                <div class="inspector-row"><span class="inspector-label">Source</span><span class="inspector-value">${sourceNode?.name || missile.source}</span></div>
                <div class="inspector-row"><span class="inspector-label">Target</span><span class="inspector-value">${targetNode?.name || missile.target}</span></div>
                <div class="inspector-row"><span class="inspector-label">Launch Tick</span><span class="inspector-value">${missile.launchTick}</span></div>
                <div class="inspector-row"><span class="inspector-label">Impact Tick</span><span class="inspector-value">${missile.impactTick}</span></div>
            </div>
        `;
    }

    getStatusClass(status) {
        switch (status) {
            case 'active': return 'good';
            case 'damaged': case 'crippled': return 'warning';
            case 'destroyed': case 'eliminated': return 'danger';
            default: return '';
        }
    }
}

if (typeof module !== 'undefined') {
    module.exports = { ScoreboardPanel, EventLogPanel, InspectorPanel };
}
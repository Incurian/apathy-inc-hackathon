/**
 * Strategic Map Renderer
 * Renders the map with cities, silos, missiles, and impact effects using SVG
 */

class MapRenderer {
    constructor(svgElement) {
        this.svg = svgElement;
        this.namespace = 'http://www.w3.org/2000/svg';
        this.selectedEntity = null;
        this.tooltip = null;
        this.missileElements = new Map();
        this.nodeElements = new Map();
        
        this.init();
    }

    init() {
        this.createDefs();
        this.createGrid();
        this.createLayers();
        this.setupInteraction();
    }

    createDefs() {
        const defs = document.createElementNS(this.namespace, 'defs');
        
        const damageGlow = document.createElementNS(this.namespace, 'filter');
        damageGlow.setAttribute('id', 'damage-glow');
        damageGlow.innerHTML = `
            <feGaussianBlur stdDeviation="2" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        `;
        defs.appendChild(damageGlow);

        const missileGlow = document.createElementNS(this.namespace, 'filter');
        missileGlow.setAttribute('id', 'missile-glow');
        missileGlow.innerHTML = `
            <feGaussianBlur stdDeviation="1.5" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        `;
        defs.appendChild(missileGlow);

        this.svg.appendChild(defs);
    }

    createGrid() {
        const gridGroup = document.createElementNS(this.namespace, 'g');
        gridGroup.classList.add('map-grid');

        for (let x = 0; x <= 800; x += 50) {
            const line = document.createElementNS(this.namespace, 'line');
            line.setAttribute('x1', x);
            line.setAttribute('y1', 0);
            line.setAttribute('x2', x);
            line.setAttribute('y2', 600);
            gridGroup.appendChild(line);
        }

        for (let y = 0; y <= 600; y += 50) {
            const line = document.createElementNS(this.namespace, 'line');
            line.setAttribute('x1', 0);
            line.setAttribute('y1', y);
            line.setAttribute('x2', 800);
            line.setAttribute('y2', y);
            gridGroup.appendChild(line);
        }

        this.svg.appendChild(gridGroup);
        this.gridGroup = gridGroup;
    }

    createLayers() {
        this.nodesLayer = document.createElementNS(this.namespace, 'g');
        this.nodesLayer.id = 'nodes-layer';
        this.svg.appendChild(this.nodesLayer);

        this.missilesLayer = document.createElementNS(this.namespace, 'g');
        this.missilesLayer.id = 'missiles-layer';
        this.svg.appendChild(this.missilesLayer);

        this.effectsLayer = document.createElementNS(this.namespace, 'g');
        this.effectsLayer.id = 'effects-layer';
        this.svg.appendChild(this.effectsLayer);

        this.labelsLayer = document.createElementNS(this.namespace, 'g');
        this.labelsLayer.id = 'labels-layer';
        this.svg.appendChild(this.labelsLayer);
    }

    setupInteraction() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'tooltip';
        document.body.appendChild(this.tooltip);

        this.svg.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.svg.addEventListener('mouseleave', () => this.hideTooltip());
        this.svg.addEventListener('click', (e) => this.handleClick(e));
    }

    handleMouseMove(e) {
        const rect = this.svg.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        let hoveredEntity = null;

        for (const [id, elem] of this.nodeElements) {
            const bbox = elem.getBBox();
            if (x >= bbox.x && x <= bbox.x + bbox.width && y >= bbox.y && y <= bbox.y + bbox.height) {
                hoveredEntity = { type: 'node', id, data: elem.dataset };
                break;
            }
        }

        if (!hoveredEntity) {
            for (const [id, elem] of this.missileElements) {
                const bbox = elem.getBBox();
                if (x >= bbox.x - 5 && x <= bbox.x + bbox.width + 5 && y >= bbox.y - 5 && y <= bbox.y + bbox.height + 5) {
                    hoveredEntity = { type: 'missile', id, data: elem.dataset };
                    break;
                }
            }
        }

        if (hoveredEntity) {
            this.showTooltip(hoveredEntity, e.clientX, e.clientY);
        } else {
            this.hideTooltip();
        }
    }

    showTooltip(entity, clientX, clientY) {
        const { type, data } = entity;
        let content = '';

        if (type === 'node') {
            content = `
                <div class="tooltip-title">${data.name} (${data.type})</div>
                <div class="tooltip-row"><span class="tooltip-label">Owner</span><span class="tooltip-value" style="color: ${data.color}">${data.ownerName}</span></div>
                <div class="tooltip-row"><span class="tooltip-label">Status</span><span class="tooltip-value">${data.status}</span></div>
                ${data.hp !== undefined ? `<div class="tooltip-row"><span class="tooltip-label">HP</span><span class="tooltip-value">${data.hp}/100</span></div>` : ''}
                ${data.population !== undefined ? `<div class="tooltip-row"><span class="tooltip-label">Population</span><span class="tooltip-value">${data.population}</span></div>` : ''}
                ${data.ammo !== undefined ? `<div class="tooltip-row"><span class="tooltip-label">Ammo</span><span class="tooltip-value">${data.ammo}</span></div>` : ''}
                ${data.cooldown !== undefined ? `<div class="tooltip-row"><span class="tooltip-label">Cooldown</span><span class="tooltip-value">${data.cooldown} ticks</span></div>` : ''}
                ${data.incomingMissiles > 0 ? `<div class="tooltip-row"><span class="tooltip-label">Incoming</span><span class="tooltip-value warning">${data.incomingMissiles}</span></div>` : ''}
            `;
        } else if (type === 'missile') {
            content = `
                <div class="tooltip-title">Missile ${data.id}</div>
                <div class="tooltip-row"><span class="tooltip-label">Owner</span><span class="tooltip-value" style="color: ${data.ownerColor}">${data.ownerName}</span></div>
                <div class="tooltip-row"><span class="tooltip-label">Target</span><span class="tooltip-value">${data.targetName}</span></div>
                <div class="tooltip-row"><span class="tooltip-label">Progress</span><span class="tooltip-value">${Math.round(data.progress * 100)}%</span></div>
                <div class="tooltip-row"><span class="tooltip-label">ETA</span><span class="tooltip-value">${Math.round(data.eta)}s</span></div>
            `;
        }

        this.tooltip.innerHTML = content;
        this.tooltip.classList.add('visible');
        this.tooltip.style.left = (clientX + 10) + 'px';
        this.tooltip.style.top = (clientY - 10) + 'px';
    }

    hideTooltip() {
        this.tooltip.classList.remove('visible');
    }

    handleClick(e) {
        const rect = this.svg.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        for (const [id, elem] of this.nodeElements) {
            const bbox = elem.getBBox();
            if (x >= bbox.x && x <= bbox.x + bbox.width && y >= bbox.y && y <= bbox.y + bbox.height) {
                this.selectEntity({ type: 'node', id, data: elem.dataset });
                return;
            }
        }

        for (const [id, elem] of this.missileElements) {
            const bbox = elem.getBBox();
            if (x >= bbox.x - 5 && x <= bbox.x + bbox.width + 5 && y >= bbox.y - 5 && y <= bbox.y + bbox.height + 5) {
                this.selectEntity({ type: 'missile', id, data: elem.dataset });
                return;
            }
        }

        this.selectEntity(null);
    }

    selectEntity(entity) {
        this.nodeElements.forEach((elem, id) => {
            elem.classList.toggle('selected', entity && entity.type === 'node' && entity.id === id);
        });

        this.missileElements.forEach((elem, id) => {
            elem.classList.toggle('selected', entity && entity.type === 'missile' && entity.id === id);
        });

        this.selectedEntity = entity;
        if (window.onEntitySelect) {
            window.onEntitySelect(entity);
        }
    }

    render(state) {
        this.renderNodes(state.nodes, state.factions);
        this.renderMissiles(state.missiles, state.factions, state.nodes);
    }

    renderNodes(nodes, factions) {
        const factionMap = new Map(factions.map(f => [f.id, f]));

        const existingIds = new Set(this.nodeElements.keys());
        const currentIds = new Set(nodes.map(n => n.id));

        for (const id of existingIds) {
            if (!currentIds.has(id)) {
                this.nodeElements.get(id).remove();
                this.nodeElements.delete(id);
            }
        }

        for (const node of nodes) {
            let elem = this.nodeElements.get(node.id);

            if (!elem) {
                elem = this.createNodeElement(node, factionMap.get(node.owner));
                this.nodesLayer.appendChild(elem);
                this.nodeElements.set(node.id, elem);
            }

            this.updateNodeElement(elem, node, factionMap.get(node.owner));
        }
    }

    createNodeElement(node, faction) {
        const group = document.createElementNS(this.namespace, 'g');
        group.classList.add('node', node.type, node.status);
        group.dataset.id = node.id;
        group.dataset.name = node.name;
        group.dataset.type = node.type;
        group.dataset.owner = node.owner;
        group.dataset.ownerName = faction?.name || node.owner;
        group.dataset.color = faction?.color || '#888';
        group.dataset.status = node.status;
        group.dataset.hp = node.hp;
        group.dataset.population = node.population;
        group.dataset.ammo = node.ammo;
        group.dataset.cooldown = node.cooldown;
        group.dataset.incomingMissiles = node.incomingMissiles || 0;

        if (node.type === 'city') {
            const circle = document.createElementNS(this.namespace, 'circle');
            circle.setAttribute('cx', node.x);
            circle.setAttribute('cy', node.y);
            circle.setAttribute('r', 12);
            circle.style.fill = faction?.color || '#888';
            group.appendChild(circle);

            if (node.status === 'damaged') {
                const ring = document.createElementNS(this.namespace, 'circle');
                ring.setAttribute('cx', node.x);
                ring.setAttribute('cy', node.y);
                ring.setAttribute('r', 14);
                ring.setAttribute('fill', 'none');
                ring.setAttribute('stroke', '#d29922');
                ring.setAttribute('stroke-width', '2');
                ring.setAttribute('stroke-dasharray', '4 4');
                group.appendChild(ring);
            }
        } else if (node.type === 'silo') {
            const rect = document.createElementNS(this.namespace, 'rect');
            rect.setAttribute('x', node.x - 10);
            rect.setAttribute('y', node.y - 10);
            rect.setAttribute('width', 20);
            rect.setAttribute('height', 20);
            rect.setAttribute('rx', 2);
            rect.style.fill = faction?.color || '#888';
            group.appendChild(rect);

            const line = document.createElementNS(this.namespace, 'line');
            line.setAttribute('x1', node.x);
            line.setAttribute('y1', node.y - 6);
            line.setAttribute('x2', node.x);
            line.setAttribute('y2', node.y + 6);
            line.setAttribute('stroke', '#000');
            line.setAttribute('stroke-width', '3');
            line.setAttribute('stroke-linecap', 'round');
            group.appendChild(line);

            const line2 = document.createElementNS(this.namespace, 'line');
            line2.setAttribute('x1', node.x - 6);
            line2.setAttribute('y1', node.y);
            line2.setAttribute('x2', node.x + 6);
            line2.setAttribute('y2', node.y);
            line2.setAttribute('stroke', '#000');
            line2.setAttribute('stroke-width', '3');
            line2.setAttribute('stroke-linecap', 'round');
            group.appendChild(line2);
        }

        if (node.status === 'destroyed') {
            group.style.opacity = '0.3';
        }

        const label = document.createElementNS(this.namespace, 'text');
        label.classList.add('node-label');
        label.setAttribute('x', node.x);
        label.setAttribute('y', node.y + (node.type === 'city' ? 20 : 22));
        label.textContent = node.name.split(' ')[0].substring(0, 3).toUpperCase();
        this.labelsLayer.appendChild(label);
        group.labelElement = label;

        return group;
    }

    updateNodeElement(elem, node, faction) {
        elem.classList.remove('active', 'damaged', 'destroyed');
        elem.classList.add(node.status);
        elem.dataset.status = node.status;
        elem.dataset.hp = node.hp;
        elem.dataset.population = node.population;
        elem.dataset.ammo = node.ammo;
        elem.dataset.cooldown = node.cooldown;
        elem.dataset.incomingMissiles = node.incomingMissiles || 0;

        const shape = elem.firstElementChild;
        if (shape) {
            shape.style.fill = faction?.color || '#888';
        }

        if (elem.labelElement) {
            elem.labelElement.textContent = node.name.split(' ')[0].substring(0, 3).toUpperCase();
        }
    }

    renderMissiles(missiles, factions, nodes) {
        const factionMap = new Map(factions.map(f => [f.id, f]));
        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        const existingIds = new Set(this.missileElements.keys());
        const currentIds = new Set(missiles.map(m => m.id));

        for (const id of existingIds) {
            if (!currentIds.has(id)) {
                this.animateMissileRemoval(this.missileElements.get(id));
                this.missileElements.delete(id);
            }
        }

        for (const missile of missiles) {
            let elem = this.missileElements.get(missile.id);

            const sourceNode = nodeMap.get(missile.source);
            const targetNode = nodeMap.get(missile.target);
            const faction = factionMap.get(missile.owner);

            if (!elem) {
                elem = this.createMissileElement(missile, faction, sourceNode, targetNode);
                this.missilesLayer.appendChild(elem);
                this.missileElements.set(missile.id, elem);
            }

            this.updateMissileElement(elem, missile, faction, sourceNode, targetNode);
        }
    }

    createMissileElement(missile, faction, sourceNode, targetNode) {
        const group = document.createElementNS(this.namespace, 'g');
        group.classList.add('missile');
        group.dataset.id = missile.id;
        group.dataset.owner = missile.owner;
        group.dataset.ownerName = faction?.name || missile.owner;
        group.dataset.ownerColor = faction?.color || '#888';
        group.dataset.target = missile.target;
        group.dataset.targetName = targetNode?.name || missile.target;
        group.dataset.progress = missile.progress;
        group.dataset.eta = ((missile.impactTick - missile.currentTick) * 0.25).toFixed(1);

        const trail = document.createElementNS(this.namespace, 'line');
        trail.classList.add('trail');
        if (sourceNode && targetNode) {
            trail.setAttribute('x1', sourceNode.x);
            trail.setAttribute('y1', sourceNode.y);
            trail.setAttribute('x2', targetNode.x);
            trail.setAttribute('y2', targetNode.y);
            trail.style.stroke = faction?.color || '#888';
        }
        group.appendChild(trail);

        const head = document.createElementNS(this.namespace, 'circle');
        head.classList.add('head');
        head.setAttribute('r', 3);
        head.style.fill = faction?.color || '#888';
        head.style.filter = 'url(#missile-glow)';
        group.appendChild(head);

        return group;
    }

    updateMissileElement(elem, missile, faction, sourceNode, targetNode) {
        elem.dataset.progress = missile.progress;
        elem.dataset.eta = ((missile.impactTick - missile.currentTick) * 0.25).toFixed(1);

        const head = elem.querySelector('.head');
        const trail = elem.querySelector('.trail');

        if (sourceNode && targetNode && head) {
            const x = sourceNode.x + (targetNode.x - sourceNode.x) * missile.progress;
            const y = sourceNode.y + (targetNode.y - sourceNode.y) * missile.progress;
            head.setAttribute('cx', x);
            head.setAttribute('cy', y);
        }

        if (missile.status === 'impact' && !elem.classList.contains('impact')) {
            this.createImpactEffect(missile, faction, targetNode);
            elem.classList.add('impact');
            setTimeout(() => elem.remove(), 500);
        }
    }

    createImpactEffect(missile, faction, targetNode) {
        if (!targetNode) return;

        const flash = document.createElementNS(this.namespace, 'circle');
        flash.setAttribute('cx', targetNode.x);
        flash.setAttribute('cy', targetNode.y);
        flash.setAttribute('r', 4);
        flash.setAttribute('fill', faction?.color || '#f85149');
        flash.classList.add('missile', 'impact');
        this.effectsLayer.appendChild(flash);

        const ring = document.createElementNS(this.namespace, 'circle');
        ring.setAttribute('cx', targetNode.x);
        ring.setAttribute('cy', targetNode.y);
        ring.setAttribute('r', 4);
        ring.setAttribute('fill', 'none');
        ring.setAttribute('stroke', faction?.color || '#f85149');
        ring.setAttribute('stroke-width', '2');
        ring.style.animation = 'impact-ring 0.6s ease-out forwards';
        this.effectsLayer.appendChild(ring);

        setTimeout(() => {
            flash.remove();
            ring.remove();
        }, 1000);
    }

    animateMissileRemoval(elem) {
        elem.style.transition = 'opacity 0.3s ease';
        elem.style.opacity = '0';
        setTimeout(() => elem.remove(), 300);
    }

    updateMatchInfo(match) {
        document.getElementById('matchId').textContent = match.matchId || 'No Match';
        document.getElementById('timer').textContent = this.formatTime(match.timeRemainingSec);
        document.getElementById('lifecycleBadge').textContent = match.lifecycleState.toUpperCase();
        document.getElementById('lifecycleBadge').className = 'lifecycle-badge ' + match.lifecycleState;
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

window.MapRenderer = MapRenderer;
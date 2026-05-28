"""
Game rules and validation logic for the DEFCON-inspired simulation.
Contains pure functions for validating actions, resolving combat, and updating game state.
"""

from typing import List, Tuple, Optional, Dict
from .models import (
    MatchState, FactionStatus, LifecycleState, ActionType, 
    EntityType, MissileStatus, Constants, Event, Faction, Node, Missile, Position
)
import math


def validate_launch_action(match_state: MatchState, faction_id: str, 
                          source_node_id: str, target_node_id: str) -> Tuple[bool, str]:
    """
    Validate if a launch action is legal for the given faction.
    Returns (is_valid, error_message)
    """
    # Check if match is running
    if match_state.lifecycle_state != LifecycleState.RUNNING:
        return False, "Match is not running"
    
    # Check if faction exists and is active
    if faction_id not in match_state.factions:
        return False, f"Faction {faction_id} does not exist"
    
    faction = match_state.factions[faction_id]
    if faction.status not in [FactionStatus.ACTIVE, FactionStatus.CRIPPLED]:
        return False, f"Faction {faction_id} is {faction_status.value} and cannot act"
    
    # Check if faction has launch capability (not crippled)
    if faction.status == FactionStatus.CRIPPLED:
        return False, f"Faction {faction_id} is crippled and has no launch capability"
    
    # Check if source node exists and belongs to faction
    if source_node_id not in match_state.nodes:
        return False, f"Source node {source_node_id} does not exist"
    
    source_node = match_state.nodes[source_node_id]
    if source_node.owner != faction_id:
        return False, f"Source node {source_node_id} does not belong to faction {faction_id}"
    
    if source_node.type != EntityType.SILO:
        return False, f"Source node {source_node_id} is not a silo"
    
    if source_node.status != "active":
        return False, f"Source node {source_node_id} is destroyed"
    
    # Check if silo has ammo
    if source_node.ammo <= 0:
        return False, f"Source node {source_node_id} has no ammo"
    
    # Check if silo is off cooldown
    if source_node.cooldown > 0:
        return False, f"Source node {source_node_id} is on cooldown"
    
    # Check if target node exists
    if target_node_id not in match_state.nodes:
        return False, f"Target node {target_node_id} does not exist"
    
    target_node = match_state.nodes[target_node_id]
    if target_node.type not in [EntityType.CITY, EntityType.SILO]:
        return False, f"Target node {target_node_id} is not a valid target"
    
    # Cannot target own nodes (optional rule - could allow friendly fire)
    if target_node.owner == faction_id:
        return False, f"Cannot target own node {target_node_id}"
    
    return True, ""


def validate_hold_action(match_state: MatchState, faction_id: str) -> Tuple[bool, str]:
    """
    Validate if a hold action is legal for the given faction.
    Hold is always legal if faction can act.
    """
    # Check if match is running
    if match_state.lifecycle_state != LifecycleState.RUNNING:
        return False, "Match is not running"
    
    # Check if faction exists
    if faction_id not in match_state.factions:
        return False, f"Faction {faction_id} does not exist"
    
    faction = match_state.factions[faction_id]
    if faction.status == FactionStatus.ELIMINATED:
        return False, f"Faction {faction_id} is eliminated and cannot act"
    
    return True, ""


def resolve_launch_action(match_state: MatchState, faction_id: str,
                         source_node_id: str, target_node_id: str) -> List[Event]:
    """
    Resolve a valid launch action. Returns list of events generated.
    Precondition: Action has been validated as legal.
    """
    events = []
    
    # Get nodes
    source_node = match_state.nodes[source_node_id]
    target_node = match_state.nodes[target_node_id]
    
    # Consume ammo
    source_node.ammo -= 1
    
    # Set cooldown
    source_node.cooldown = Constants.DECISION_WINDOW_TICKS  # 4 seconds cooldown
    
    # Generate missile ID
    missile_id = f"m-{len(match_state.missiles) + 1}-{match_state.tick}"
    
    # Create missile entity
    missile = Missile(
        id=missile_id,
        owner=faction_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        launch_tick=match_state.tick,
        impact_tick=match_state.tick + Constants.MISSILE_FLIGHT_TIME_TICKS,
        current_position=Position(
            x=source_node.position.x,
            y=source_node.position.y
        ),
        status=MissileStatus.FLYING
    )
    
    match_state.missiles[missile_id] = missile
    
    # Create launch event
    launch_event = Event(
        tick=match_state.tick,
        type="launch",
        faction_id=faction_id,
        missile_id=missile_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        details={
            "source": source_node.name,
            "target": target_node.name
        }
    )
    
    match_state.events.append(launch_event)
    events.append(launch_event)
    
    # Update faction's last action
    faction = match_state.factions[faction_id]
    faction.last_action = {
        "type": "launch",
        "from": source_node_id,
        "target": target_node_id
    }
    
    return events


def resolve_hold_action(match_state: MatchState, faction_id: str) -> List[Event]:
    """
    Resolve a hold action. Returns list of events generated.
    """
    events = []
    
    # Create hold event
    hold_event = Event(
        tick=match_state.tick,
        type="hold",
        faction_id=faction_id,
        details={"reason": "no action"}
    )
    
    match_state.events.append(hold_event)
    events.append(hold_event)
    
    # Update faction's last action
    faction = match_state.factions[faction_id]
    faction.last_action = {
        "type": "hold"
    }
    
    return events


def update_missiles(match_state: MatchState) -> List[Event]:
    """
    Update missile positions and check for impacts.
    Returns list of impact events.
    """
    impact_events = []
    missiles_to_remove = []
    
    for missile_id, missile in match_state.missiles.items():
        if missile.status != MissileStatus.FLYING:
            continue
            
        # Check if missile has reached impact tick
        if match_state.tick >= missile.impact_tick:
            # Resolve impact
            target_node = match_state.nodes[missile.target_node_id]
            
            # Apply damage
            target_node.hp -= Constants.MISSILE_DAMAGE
            
            # Check if target is destroyed (one-hit in MVP)
            if target_node.hp <= 0:
                target_node.hp = 0
                target_node.status = "destroyed"
                
                # Update population for cities
                if target_node.type == EntityType.CITY:
                    target_node.population = 0
                    
                    # Update owning faction's population
                    owner_faction = match_state.factions[target_node.owner]
                    # Recalculate total population for faction
                    total_pop = 0
                    for node_id, node in match_state.nodes.items():
                        if node.owner == owner_faction.id and node.type == EntityType.CITY:
                            total_pop += node.population
                    owner_faction.population = total_pop
                
                # Create destruction event
                destruction_event = Event(
                    tick=match_state.tick,
                    type="destruction",
                    faction_id=target_node.owner,
                    target_node_id=target_node.target_node_id if hasattr(target_node, 'target_node_id') else None,
                    source_node_id=missile.source_node_id,
                    details={
                        "destroyed_entity": target_node.name,
                        "entity_type": target_node.type.value,
                        "destroying_faction": missile.owner
                    }
                )
                
                match_state.events.append(destruction_event)
                impact_events.append(destruction_event)
                
                # Check if this destruction eliminates a faction
                check_faction_elimination(match_state, target_node.owner)
            
            # Create impact event
            impact_event = Event(
                tick=match_state.tick,
                type="impact",
                faction_id=missile.owner,
                missile_id=missile_id,
                target_node_id=missile.target_node_id,
                damage=Constants.MISSILE_DAMAGE,
                details={
                    "impact_location": f"({target_node.position.x}, {target_node.position.y})",
                    "target_name": target_node.name
                }
            )
            
            match_state.events.append(impact_event)
            impact_events.append(impact_event)
            
            # Mark missile for removal (it has impacted)
            missile.status = MissileStatus.IMPACT
            missiles_to_remove.append(missile_id)
        else:
            # Update missile position (linear interpolation for simplicity)
            source_node = match_state.nodes[missile.source_node_id]
            target_node = match_state.nodes[missile.target_node_id]
            
            # Calculate progress (0.0 to 1.0)
            ticks_since_launch = match_state.tick - missile.launch_tick
            total_ticks = Constants.MISSILE_FLIGHT_TIME_TICKS
            progress = min(ticks_since_launch / total_ticks, 1.0)
            
            # Interpolate position
            missile.current_position.x = int(
                source_node.position.x + 
                (target_node.position.x - source_node.position.x) * progress
            )
            missile.current_position.y = int(
                source_node.position.y + 
                (target_node.position.y - source_node.position.y) * progress
            )
    
    # Remove impacted missiles (optional - could keep them for visual effect)
    # for missile_id in missiles_to_remove:
    #     del match_state.missiles[missile_id]
    
    return impact_events


def update_cooldowns(match_state: MatchState) -> None:
    """
    Update cooldown timers for all silos.
    """
    for node in match_state.nodes.values():
        if node.type == EntityType.SILO and node.cooldown > 0:
            node.cooldown -= 1


def update_faction_statuses(match_state: MatchState) -> None:
    """
    Update faction statuses based on current state.
    """
    for faction in match_state.factions.values():
        if faction.status == FactionStatus.ELIMINATED:
            continue
            
        # Count surviving cities and silos with ammo
        surviving_cities = 0
        launch_capable_silos = 0
        
        for node_id, node in match_state.nodes.items():
            if node.owner == faction.id:
                if node.type == EntityType.CITY and node.status == "active" and node.population > 0:
                    surviving_cities += 1
                elif node.type == EntityType.SILO and node.status == "active" and node.ammo > 0 and node.cooldown == 0:
                    launch_capable_silos += 1
        
        # Update faction population (recalculate from cities)
        total_population = 0
        for node_id, node in match_state.nodes.items():
            if node.owner == faction.id and node.type == EntityType.CITY:
                total_population += node.population
        faction.population = total_population
        
        # Determine status
        if surviving_cities == 0 or total_population == 0:
            faction.status = FactionStatus.ELIMINATED
        elif launch_capable_silos == 0:
            faction.status = FactionStatus.CRIPPLED
        else:
            faction.status = FactionStatus.ACTIVE


def check_match_end(match_state: MatchState) -> bool:
    """
    Check if the match has ended.
    Returns True if match should end, False otherwise.
    """
    # Check time limit
    if match_state.time_remaining_sec <= 0:
        return True
    
    # Check if only one faction has surviving cities
    factions_with_cities = 0
    for faction in match_state.factions.values():
        surviving_cities = 0
        for node_id, node in match_state.nodes.items():
            if node.owner == faction.id and node.type == EntityType.CITY and node.status == "active":
                surviving_cities += 1
        if surviving_cities > 0:
            factions_with_cities += 1
    
    return factions_with_cities <= 1


def check_faction_elimination(match_state: MatchState, faction_id: str) -> None:
    """
    Check if a faction has been eliminated and update its status.
    """
    if faction_id not in match_state.factions:
        return
        
    faction = match_state.factions[faction_id]
    if faction.status == FactionStatus.ELIMINATED:
        return
    
    # Check if faction has any surviving cities or population
    surviving_cities = 0
    total_population = 0
    
    for node_id, node in match_state.nodes.items():
        if node.owner == faction_id:
            if node.type == EntityType.CITY and node.status == "active":
                surviving_cities += 1
                total_population += node.population
    
    if surviving_cities == 0 or total_population == 0:
        faction.status = FactionStatus.ELIMINATED
        
        # Create elimination event
        elimination_event = Event(
            tick=match_state.tick,
            type="faction_eliminated",
            faction_id=faction_id,
            details={
                "eliminated_faction": faction.name,
                "reason": "no_surviving_cities_or_population"
            }
        )
        
        match_state.events.append(elimination_event)


def advance_tick(match_state: MatchState) -> List[Event]:
    """
    Advance the simulation by one tick.
    Returns list of events generated during this tick.
    """
    events = []
    
    # Decrement time remaining
    if match_state.time_remaining_sec > 0:
        match_state.time_remaining_sec -= Constants.TICK_MS / 1000.0
    
    # Update missile positions and check for impacts
    impact_events = update_missiles(match_state)
    events.extend(impact_events)
    
    # Update cooldowns
    update_cooldowns(match_state)
    
    # Update faction statuses
    update_faction_statuses(match_state)
    
    # Check for match end
    if check_match_end(match_state):
        if match_state.lifecycle_state == LifecycleState.RUNNING:
            match_state.lifecycle_state = LifecycleState.FINISHED
            
            # Create match end event
            # Determine winner
            winner_id = None
            highest_score = -1
            
            for faction_id, faction in match_state.factions.items():
                if faction.score > highest_score:
                    highest_score = faction.score
                    winner_id = faction_id
                elif faction.score == highest_score and winner_id is not None:
                    # Tie - could implement tie-breakers here
                    pass
            
            match_end_event = Event(
                tick=match_state.tick,
                type="match_end",
                details={
                    "winner": winner_id,
                    "winning_score": highest_score if winner_id else 0,
                    "reason": "time_expired" if match_state.time_remaining_sec <= 0 else "one_faction_remaining"
                }
            )
            
            match_state.events.append(match_end_event)
            events.append(match_end_event)
    
    # Increment tick counter
    match_state.tick += 1
    
    # Generate snapshot for replay every 4 ticks (once per second)
    if match_state.tick % 4 == 0:
        match_state.snapshot_tick = match_state.tick
    
    return events


def apply_action(match_state: MatchState, faction_id: str, action: dict) -> List[Event]:
    """
    Apply an action for a faction. Returns list of events generated.
    Handles validation and resolution.
    """
    events = []
    
    action_type = action.get("type")
    
    if action_type == ActionType.HOLD.value:
        is_valid, error_msg = validate_hold_action(match_state, faction_id)
        if is_valid:
            events = resolve_hold_action(match_state, faction_id)
        else:
            # Create invalid action event
            invalid_event = Event(
                tick=match_state.tick,
                type="invalid_action",
                faction_id=faction_id,
                details={
                    "attempted_action": action,
                    "reason": error_msg
                }
            )
            match_state.events.append(invalid_event)
            events.append(invalid_event)
            
    elif action_type == ActionType.LAUNCH.value:
        source_node_id = action.get("from")
        target_node_id = action.get("target")
        
        if source_node_id is None or target_node_id is None:
            # Create invalid action event for malformed action
            invalid_event = Event(
                tick=match_state.tick,
                type="invalid_action",
                faction_id=faction_id,
                details={
                    "attempted_action": action,
                    "reason": "missing 'from' or 'target' field"
                }
            )
            match_state.events.append(invalid_event)
            events.append(invalid_event)
        else:
            is_valid, error_msg = validate_launch_action(match_state, faction_id, source_node_id, target_node_id)
            if is_valid:
                events = resolve_launch_action(match_state, faction_id, source_node_id, target_node_id)
            else:
                # Create invalid action event
                invalid_event = Event(
                    tick=match_state.tick,
                    type="invalid_action",
                    faction_id=faction_id,
                    details={
                        "attempted_action": action,
                        "reason": error_msg
                    }
                )
                match_state.events.append(invalid_event)
                events.append(invalid_event)
    else:
        # Unknown action type
        invalid_event = Event(
            tick=match_state.tick,
            type="invalid_action",
            faction_id=faction_id,
            details={
                "attempted_action": action,
                "reason": f"unknown action type: {action_type}"
            }
        )
        match_state.events.append(invalid_event)
        events.append(invalid_event)
    
    return events


def initialize_match(scenario_name: str = "default") -> MatchState:
    """
    Initialize a new match state from the default scenario.
    """
    import uuid
    from datetime import datetime
    
    match_id = f"match-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    match_state = MatchState(
        match_id=match_id,
        tick=0,
        time_remaining_sec=Constants.MATCH_DURATION_SEC,
        lifecycle_state=LifecycleState.IDLE
    )
    
    # Initialize factions
    for faction_config in Constants.FACTION_CONFIGS:
        faction = Faction(
            id=faction_config["id"],
            name=faction_config["name"],
            color=faction_config["color"],
            population=0,  # Will be set after cities are created
            score=0,
            status=FactionStatus.ACTIVE,
            control_mode="scripted"  # Default to scripted bots
        )
        match_state.factions[faction_config["id"]] = faction
    
    # Initialize nodes (cities and silos)
    for node_id, coords in Constants.MAP_COORDINATES.items():
        # Determine faction from node_id prefix
        faction_id = node_id.split('-')[0]
        
        if "city" in node_id:
            node = Node(
                id=node_id,
                name=coords["name"],
                owner=faction_id,
                type=EntityType.CITY,
                position=Position(x=coords["x"], y=coords["y"]),
                hp=Constants.CITY_HP,
                population=Constants.INITIAL_CITY_POPULATION,
                status="active"
            )
            
            # Add to faction's owned sites
            match_state.factions[faction_id].owned_sites.append(node_id)
            
        elif "silo" in node_id:
            node = Node(
                id=node_id,
                name=coords["name"],
                owner=faction_id,
                type=EntityType.SILO,
                position=Position(x=coords["x"], y=coords["y"]),
                hp=Constants.SILO_HP,
                ammo=Constants.INITIAL_SILO_AMMO,
                cooldown=0,
                status="active"
            )
            
            # Add to faction's owned sites
            match_state.factions[faction_id].owned_sites.append(node_id)
        
        match_state.nodes[node_id] = node
    
    # Calculate initial faction populations from cities
    for faction in match_state.factions.values():
        total_pop = 0
        for node_id, node in match_state.nodes.items():
            if node.owner == faction.id and node.type == EntityType.CITY:
                total_pop += node.population
        faction.population = total_pop
    
    # Set initial lifecycle state
    match_state.lifecycle_state = LifecycleState.IDLE
    
    # Create match start event
    start_event = Event(
        tick=0,
        type="match_start",
        details={
            "scenario": scenario_name,
            "match_id": match_id
        }
    )
    
    match_state.events.append(start_event)
    
    return match_state
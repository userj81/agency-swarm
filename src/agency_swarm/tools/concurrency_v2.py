"""
Advanced concurrency management for Agency Swarm.

This module provides the GlobalConcurrencyManager for managing tool execution
constraints across multiple agents with deadlock detection, auto-resolution,
and real-time event tracking.
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid
import threading


# ============================================================================
# Enums and Constants
# ============================================================================

class ExecutionStage(Enum):
    """Stage of lock execution lifecycle."""
    ACQUIRED = "acquired"
    EXECUTING = "executing"
    RELEASING = "releasing"


class ConflictType(Enum):
    """Type of conflict event."""
    DEADLOCK = "deadlock"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PRIORITY_INVERSION = "priority_inversion"


class DeadlockResolutionStrategy(Enum):
    """Strategy for resolving deadlocks."""
    PRIORITY_BASED = "priority"  # Kill lock of lowest priority
    YOUNGEST_FIRST = "youngest"  # Kill most recent lock
    OLDEST_FIRST = "oldest"  # Kill oldest lock
    RANDOM_VICTIM = "random"  # Choose randomly
    MANUAL_INTERVENTION = "manual"  # Require human decision


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class PendingLockRequest:
    """Represents a pending lock request in the waiting queue."""
    request_id: str
    agent_name: str
    tool_name: str
    priority: int
    requested_at: float
    retry_count: int = 0
    timeout_seconds: float = 30.0

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "priority": self.priority,
            "requested_at": self.requested_at,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "waiting_duration": time.time() - self.requested_at,
        }


@dataclass
class AgentLockState:
    """Represents the current state of an agent's tool lock."""
    agent_name: str
    tool_name: str
    lock_id: str
    acquired_at: float
    expires_at: Optional[float]
    priority: int
    owner_thread_id: Optional[int]
    retry_count: int = 0
    waiting_queue: List[PendingLockRequest] = field(default_factory=list)
    execution_stage: ExecutionStage = ExecutionStage.ACQUIRED

    @property
    def duration_seconds(self) -> float:
        """Get duration of lock in seconds."""
        return time.time() - self.acquired_at

    @property
    def is_expired(self) -> bool:
        """Check if lock has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "lock_id": self.lock_id,
            "acquired_at": self.acquired_at,
            "acquired_at_iso": datetime.fromtimestamp(self.acquired_at, tz=timezone.utc).isoformat(),
            "expires_at": self.expires_at,
            "expires_at_iso": datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat() if self.expires_at else None,
            "priority": self.priority,
            "owner_thread_id": self.owner_thread_id,
            "retry_count": self.retry_count,
            "waiting_queue": [req.to_dict() for req in self.waiting_queue],
            "duration_seconds": self.duration_seconds,
            "execution_stage": self.execution_stage.value,
        }


@dataclass
class LockEvent:
    """Represents a lock lifecycle event."""
    event_id: str
    timestamp: float
    event_type: str  # acquired, released, timeout, etc.
    agent_name: str
    tool_name: str
    lock_id: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "lock_id": self.lock_id,
            "details": self.details,
        }


@dataclass
class ConflictEvent:
    """Represents a conflict detection event."""
    conflict_id: str
    timestamp: float
    conflict_type: ConflictType
    involved_agents: List[str]
    description: str
    resolution: Optional[str] = None
    auto_resolved: bool = False
    resolved_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "conflict_id": self.conflict_id,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "conflict_type": self.conflict_type.value,
            "involved_agents": self.involved_agents,
            "description": self.description,
            "resolution": self.resolution,
            "auto_resolved": self.auto_resolved,
            "resolved_at": self.resolved_at,
            "resolved_at_iso": datetime.fromtimestamp(self.resolved_at, tz=timezone.utc).isoformat() if self.resolved_at else None,
        }


@dataclass
class DeadlockInfo:
    """Information about a detected deadlock."""
    cycle: List[str]  # List of agent names forming the cycle
    detected_at: float
    deadlock_id: str
    involved_locks: List[str]
    severity: str = "high"  # low, medium, high

    def to_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "detected_at": self.detected_at,
            "detected_at_iso": datetime.fromtimestamp(self.detected_at, tz=timezone.utc).isoformat(),
            "deadlock_id": self.deadlock_id,
            "involved_locks": self.involved_locks,
            "severity": self.severity,
        }


@dataclass
class ConflictPattern:
    """Represents a recurring conflict pattern between agents."""
    agent_a: str
    agent_b: str
    conflict_count: int
    last_conflict: float
    avg_resolution_time: float

    def to_dict(self) -> dict:
        return {
            "agent_a": self.agent_a,
            "agent_b": self.agent_b,
            "conflict_count": self.conflict_count,
            "last_conflict_iso": datetime.fromtimestamp(self.last_conflict, tz=timezone.utc).isoformat(),
            "avg_resolution_time": self.avg_resolution_time,
        }


@dataclass
class ConcurrencyAnalytics:
    """Analytics data for concurrency patterns."""
    total_locks_acquired: int = 0
    total_locks_released: int = 0
    conflicts_detected: int = 0
    deadlocks_resolved: int = 0
    most_locked_agents: List[Tuple[str, int]] = field(default_factory=list)
    conflict_hotspots: List[Tuple[str, str, int]] = field(default_factory=list)  # (agent_a, agent_b, count)
    peak_concurrency_time: Optional[str] = None
    avg_lock_duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_locks_acquired": self.total_locks_acquired,
            "total_locks_released": self.total_locks_released,
            "conflicts_detected": self.conflicts_detected,
            "deadlocks_resolved": self.deadlocks_resolved,
            "most_locked_agents": [{"agent": a, "count": c} for a, c in self.most_locked_agents],
            "conflict_hotspots": [{"agent_a": a, "agent_b": b, "count": c} for a, b, c in self.conflict_hotspots],
            "peak_concurrency_time": self.peak_concurrency_time,
            "avg_lock_duration": self.avg_lock_duration,
        }


# ============================================================================
# Deadlock Detector
# ============================================================================

class DeadlockDetector:
    """
    Detects deadlocks using wait-for graph analysis with DFS cycle detection.
    """

    def __init__(self, resolution_strategy: DeadlockResolutionStrategy = DeadlockResolutionStrategy.PRIORITY_BASED):
        self.wait_for_graph: Dict[str, Set[str]] = {}  # agent -> set of agents it's waiting for
        self.resolution_strategy = resolution_strategy
        self._lock = threading.Lock()

    def update_wait_for_graph(self, waiting_agent: str, blocking_agent: str):
        """Update the wait-for graph with a new waiting relationship."""
        with self._lock:
            if waiting_agent not in self.wait_for_graph:
                self.wait_for_graph[waiting_agent] = set()
            self.wait_for_graph[waiting_agent].add(blocking_agent)

    def remove_from_graph(self, agent: str):
        """Remove an agent from the wait-for graph."""
        with self._lock:
            # Remove outgoing edges
            if agent in self.wait_for_graph:
                del self.wait_for_graph[agent]
            # Remove incoming edges
            for other_agents in self.wait_for_graph.values():
                other_agents.discard(agent)

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in the wait-for graph using DFS.
        Returns a list of cycles (each cycle is a list of agent names).
        """
        with self._lock:
            cycles = []
            visited = set()
            rec_stack = set()
            path = []

            def dfs(node: str) -> bool:
                visited.add(node)
                rec_stack.add(node)
                path.append(node)

                for neighbor in self.wait_for_graph.get(node, set()):
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        # Found a cycle - extract it
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)
                        return True

                path.pop()
                rec_stack.remove(node)
                return False

            for node in list(self.wait_for_graph.keys()):
                if node not in visited:
                    dfs(node)

            return cycles

    def get_deadlock_info(self, cycle: List[str], locks: Dict[str, AgentLockState]) -> DeadlockInfo:
        """Create DeadlockInfo from a detected cycle."""
        involved_locks = []
        for agent in cycle[:-1]:  # Exclude the duplicate at the end
            if agent in locks:
                involved_locks.append(locks[agent].lock_id)

        return DeadlockInfo(
            cycle=cycle,
            detected_at=time.time(),
            deadlock_id=str(uuid.uuid4()),
            involved_locks=involved_locks,
            severity=self._calculate_severity(cycle, locks),
        )

    def _calculate_severity(self, cycle: List[str], locks: Dict[str, AgentLockState]) -> str:
        """Calculate deadlock severity based on cycle length and lock durations."""
        cycle_len = len(cycle) - 1  # Exclude duplicate

        if cycle_len >= 4:
            return "high"
        elif cycle_len >= 3:
            return "medium"
        else:
            return "low"


# ============================================================================
# Conflict Pattern Detector
# ============================================================================

class ConflictPatternDetector:
    """Detects recurring conflict patterns between agents."""

    def __init__(self, history_size: int = 1000):
        self.conflict_matrix: Dict[Tuple[str, str], int] = {}
        self.resolution_times: Dict[Tuple[str, str], List[float]] = {}
        self.last_conflict: Dict[Tuple[str, str], float] = {}
        self._lock = threading.Lock()

    def record_conflict(self, agent_a: str, agent_b: str, resolution_time: float):
        """Record a conflict between two agents."""
        # Normalize key (alphabetical order)
        key = tuple(sorted([agent_a, agent_b]))

        with self._lock:
            self.conflict_matrix[key] = self.conflict_matrix.get(key, 0) + 1
            if key not in self.resolution_times:
                self.resolution_times[key] = []
            self.resolution_times[key].append(resolution_time)
            self.last_conflict[key] = time.time()

    def get_hotspots(self, top_n: int = 10) -> List[ConflictPattern]:
        """Get top N conflict hotspots."""
        with self._lock:
            sorted_conflicts = sorted(
                self.conflict_matrix.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]

            patterns = []
            for (agent_a, agent_b), count in sorted_conflicts:
                times = self.resolution_times.get((agent_a, agent_b), [])
                avg_time = sum(times) / len(times) if times else 0.0
                last = self.last_conflict.get((agent_a, agent_b), time.time())

                patterns.append(ConflictPattern(
                    agent_a=agent_a,
                    agent_b=agent_b,
                    conflict_count=count,
                    last_conflict=last,
                    avg_resolution_time=avg_time,
                ))

            return patterns

    def get_conflict_count(self, agent_a: str, agent_b: str) -> int:
        """Get conflict count between two specific agents."""
        key = tuple(sorted([agent_a, agent_b]))
        return self.conflict_matrix.get(key, 0)


# ============================================================================
# Event Manager
# ============================================================================

class ConcurrencyEventManager:
    """Manages event history and callbacks for real-time updates."""

    def __init__(self, history_size: int = 1000):
        self.lock_history: deque[LockEvent] = deque(maxlen=history_size)
        self.conflict_history: deque[ConflictEvent] = deque(maxlen=history_size)
        self.event_callbacks: List[Callable] = []
        self._lock = threading.Lock()

    def record_lock_event(self, event: LockEvent):
        """Record a lock event and notify listeners."""
        with self._lock:
            self.lock_history.append(event)

        # Notify listeners outside the lock
        for callback in self.event_callbacks:
            try:
                callback({"type": "lock_event", "data": event.to_dict()})
            except Exception:
                pass  # Don't let callback errors break the flow

    def record_conflict_event(self, event: ConflictEvent):
        """Record a conflict event and notify listeners."""
        with self._lock:
            self.conflict_history.append(event)

        for callback in self.event_callbacks:
            try:
                callback({"type": "conflict_event", "data": event.to_dict()})
            except Exception:
                pass

    def register_callback(self, callback: Callable):
        """Register a callback for real-time events."""
        self.event_callbacks.append(callback)

    def unregister_callback(self, callback: Callable):
        """Unregister a callback."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)

    def get_lock_history(self, limit: int = 100) -> List[dict]:
        """Get recent lock history."""
        with self._lock:
            history = list(self.lock_history)[-limit:]
        return [e.to_dict() for e in history]

    def get_conflict_history(self, limit: int = 50) -> List[dict]:
        """Get recent conflict history."""
        with self._lock:
            history = list(self.conflict_history)[-limit:]
        return [e.to_dict() for e in history]


# ============================================================================
# Global Concurrency Manager
# ============================================================================

class GlobalConcurrencyManager:
    """
    Centralized concurrency manager for Agency Swarm.

    Manages locks across multiple agents with deadlock detection,
    auto-resolution, and real-time event tracking.
    """

    def __init__(
        self,
        resolution_strategy: DeadlockResolutionStrategy = DeadlockResolutionStrategy.PRIORITY_BASED,
        default_timeout: float = 30.0,
        max_retry_attempts: int = 3,
        enable_auto_resolution: bool = True,
    ):
        # Lock storage
        self.locks_by_agent: Dict[str, AgentLockState] = {}
        self._locks_lock = threading.Lock()

        # Deadlock detection
        self.deadlock_detector = DeadlockDetector(resolution_strategy)

        # Conflict pattern detection
        self.pattern_detector = ConflictPatternDetector()

        # Event management
        self.event_manager = ConcurrencyEventManager()

        # Configuration
        self.default_timeout = default_timeout
        self.max_retry_attempts = max_retry_attempts
        self.enable_auto_resolution = enable_auto_resolution

        # Analytics
        self._analytics_lock = threading.Lock()
        self._lock_durations: List[float] = []

        # Background monitoring
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False

    async def acquire_lock(
        self,
        agent_name: str,
        tool_name: str,
        priority: int = 5,
        timeout: Optional[float] = None,
        owner_thread_id: Optional[int] = None,
    ) -> str:
        """
        Acquire a lock for an agent/tool combination.

        Args:
            agent_name: Name of the agent acquiring the lock
            tool_name: Name of the tool being locked
            priority: Priority level (1-10, lower is higher priority)
            timeout: Maximum time to wait for lock (None = use default)
            owner_thread_id: Thread ID of the lock owner

        Returns:
            Lock ID if acquired successfully

        Raises:
            asyncio.TimeoutError: If lock cannot be acquired within timeout
        """
        timeout = timeout or self.default_timeout
        lock_key = f"{agent_name}:{tool_name}"
        lock_id = str(uuid.uuid4())
        acquired_at = time.time()

        with self._locks_lock:
            # Check if lock already exists
            if lock_key in self.locks_by_agent:
                existing_lock = self.locks_by_agent[lock_key]

                # Create pending request
                request = PendingLockRequest(
                    request_id=str(uuid.uuid4()),
                    agent_name=agent_name,
                    tool_name=tool_name,
                    priority=priority,
                    requested_at=time.time(),
                    timeout_seconds=timeout,
                )

                existing_lock.waiting_queue.append(request)

                # Update wait-for graph
                self.deadlock_detector.update_wait_for_graph(agent_name, existing_lock.agent_name)

                # Record event
                self.event_manager.record_lock_event(LockEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=time.time(),
                    event_type="queued",
                    agent_name=agent_name,
                    tool_name=tool_name,
                    lock_id=lock_id,
                    details={"queue_position": len(existing_lock.waiting_queue)},
                ))

                # Wait for lock with timeout
                raise asyncio.TimeoutError(f"Lock {lock_key} is already held")

            # Create new lock
            lock = AgentLockState(
                agent_name=agent_name,
                tool_name=tool_name,
                lock_id=lock_id,
                acquired_at=acquired_at,
                expires_at=None,
                priority=priority,
                owner_thread_id=owner_thread_id,
                retry_count=0,
                waiting_queue=[],
                execution_stage=ExecutionStage.ACQUIRED,
            )

            self.locks_by_agent[lock_key] = lock

        # Record event
        self.event_manager.record_lock_event(LockEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="acquired",
            agent_name=agent_name,
            tool_name=tool_name,
            lock_id=lock_id,
            details={"priority": priority},
        ))

        # Update analytics
        with self._analytics_lock:
            self._update_analytics()

        return lock_id

    async def release_lock(self, lock_id: str) -> bool:
        """
        Release a lock by ID.

        Args:
            lock_id: ID of the lock to release

        Returns:
            True if lock was released, False if not found
        """
        with self._locks_lock:
            # Find the lock
            lock_key = None
            lock = None
            for key, l in self.locks_by_agent.items():
                if l.lock_id == lock_id:
                    lock_key = key
                    lock = l
                    break

            if not lock:
                return False

            # Calculate duration
            duration = lock.duration_seconds
            with self._analytics_lock:
                self._lock_durations.append(duration)

            # Remove from wait-for graph
            self.deadlock_detector.remove_from_graph(lock.agent_name)

            # Process waiting queue
            next_lock = None
            if lock.waiting_queue:
                # Sort by priority (lower number = higher priority)
                sorted_queue = sorted(lock.waiting_queue, key=lambda r: r.priority)
                next_request = sorted_queue[0]

                # Create new lock for next agent
                next_lock = AgentLockState(
                    agent_name=next_request.agent_name,
                    tool_name=next_request.tool_name,
                    lock_id=str(uuid.uuid4()),
                    acquired_at=time.time(),
                    expires_at=None,
                    priority=next_request.priority,
                    owner_thread_id=None,
                    retry_count=next_request.retry_count,
                    waiting_queue=[],
                    execution_stage=ExecutionStage.ACQUIRED,
                )

                self.locks_by_agent[lock_key] = next_lock

                # Record acquisition event
                self.event_manager.record_lock_event(LockEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=time.time(),
                    event_type="acquired_from_queue",
                    agent_name=next_request.agent_name,
                    tool_name=next_request.tool_name,
                    lock_id=next_lock.lock_id,
                    details={"previous_lock_id": lock_id, "queue_wait_time": time.time() - next_request.requested_at},
                ))
            else:
                # No waiting agents, remove lock
                del self.locks_by_agent[lock_key]

        # Record release event
        self.event_manager.record_lock_event(LockEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="released",
            agent_name=lock.agent_name,
            tool_name=lock.tool_name,
            lock_id=lock_id,
            details={"duration_seconds": duration},
        ))

        # Update analytics
        with self._analytics_lock:
            self._update_analytics()

        return True

    async def override_lock(self, lock_id: str, reason: str) -> bool:
        """
        Manually override/release a lock.

        Args:
            lock_id: ID of the lock to override
            reason: Reason for override

        Returns:
            True if lock was overridden
        """
        with self._locks_lock:
            for key, lock in list(self.locks_by_agent.items()):
                if lock.lock_id == lock_id:
                    # Release the lock
                    await self.release_lock(lock_id)

                    # Record override event
                    self.event_manager.record_lock_event(LockEvent(
                        event_id=str(uuid.uuid4()),
                        timestamp=time.time(),
                        event_type="overridden",
                        agent_name=lock.agent_name,
                        tool_name=lock.tool_name,
                        lock_id=lock_id,
                        details={"reason": reason},
                    ))

                    return True
        return False

    def get_active_locks(self) -> List[dict]:
        """Get all currently active locks."""
        with self._locks_lock:
            return [lock.to_dict() for lock in self.locks_by_agent.values()]

    def get_lock_details(self, lock_id: str) -> Optional[dict]:
        """Get details of a specific lock."""
        with self._locks_lock:
            for lock in self.locks_by_agent.values():
                if lock.lock_id == lock_id:
                    return lock.to_dict()
        return None

    def get_lock_history(self, limit: int = 100) -> List[dict]:
        """Get recent lock history."""
        return self.event_manager.get_lock_history(limit)

    def get_conflicts(self, limit: int = 50) -> List[dict]:
        """Get recent conflict history."""
        return self.event_manager.get_conflict_history(limit)

    async def detect_deadlocks(self) -> List[DeadlockInfo]:
        """
        Run deadlock detection and return any detected deadlocks.

        Returns:
            List of DeadlockInfo objects for detected deadlocks
        """
        cycles = self.deadlock_detector.detect_cycles()
        deadlocks = []

        with self._locks_lock:
            locks_snapshot = {k: v for k, v in self.locks_by_agent.items()}

        for cycle in cycles:
            deadlock = self.deadlock_detector.get_deadlock_info(cycle, locks_snapshot)
            deadlocks.append(deadlock)

            # Record conflict event
            conflict = ConflictEvent(
                conflict_id=str(uuid.uuid4()),
                timestamp=time.time(),
                conflict_type=ConflictType.DEADLOCK,
                involved_agents=cycle[:-1],  # Exclude duplicate
                description=f"Deadlock detected in cycle: {' -> '.join(cycle)}",
                resolution=None,
                auto_resolved=False,
            )
            self.event_manager.record_conflict_event(conflict)

        return deadlocks

    async def resolve_deadlock(
        self,
        cycle: List[str],
        strategy: Optional[DeadlockResolutionStrategy] = None,
        victim_lock_id: Optional[str] = None,
    ) -> bool:
        """
        Resolve a deadlock using the specified strategy.

        Args:
            cycle: List of agent names forming the deadlock cycle
            strategy: Resolution strategy to use
            victim_lock_id: Specific lock ID to release (for MANUAL strategy)

        Returns:
            True if deadlock was resolved
        """
        strategy = strategy or self.deadlock_detector.resolution_strategy

        if strategy == DeadlockResolutionStrategy.MANUAL_INTERVENTION:
            if not victim_lock_id:
                return False
            return await self.release_lock(victim_lock_id)

        # Find locks involved in the cycle
        with self._locks_lock:
            involved_locks = []
            for agent in cycle[:-1]:  # Exclude duplicate
                for lock_key, lock in self.locks_by_agent.items():
                    if lock.agent_name == agent:
                        involved_locks.append((lock_key, lock))
                        break

        if not involved_locks:
            return False

        # Select victim based on strategy
        victim_lock = None
        match strategy:
            case DeadlockResolutionStrategy.PRIORITY_BASED:
                # Kill lowest priority (highest priority number)
                victim_lock = max(involved_locks, key=lambda x: x[1].priority)[1]
            case DeadlockResolutionStrategy.YOUNGEST_FIRST:
                # Kill most recently acquired
                victim_lock = max(involved_locks, key=lambda x: x[1].acquired_at)[1]
            case DeadlockResolutionStrategy.OLDEST_FIRST:
                # Kill oldest
                victim_lock = min(involved_locks, key=lambda x: x[1].acquired_at)[1]
            case DeadlockResolutionStrategy.RANDOM_VICTIM:
                import random
                victim_lock = random.choice(involved_locks)[1]

        if victim_lock:
            await self.release_lock(victim_lock.lock_id)

            # Update conflict event
            conflict = ConflictEvent(
                conflict_id=str(uuid.uuid4()),
                timestamp=time.time(),
                conflict_type=ConflictType.DEADLOCK,
                involved_agents=cycle[:-1],
                description=f"Deadlock resolved using {strategy.value} strategy",
                resolution=strategy.value,
                auto_resolved=True,
                resolved_at=time.time(),
            )
            self.event_manager.record_conflict_event(conflict)

            return True

        return False

    def get_conflict_patterns(self, top_n: int = 10) -> List[dict]:
        """Get top conflict hotspots."""
        patterns = self.pattern_detector.get_hotspots(top_n)
        return [p.to_dict() for p in patterns]

    def get_analytics(self, time_range: str = "1h") -> dict:
        """
        Get concurrency analytics.

        Args:
            time_range: Time range for analytics (1h, 24h, 7d)

        Returns:
            ConcurrencyAnalytics as dict
        """
        with self._analytics_lock:
            return self._get_analytics_data()

    def _update_analytics(self):
        """Update analytics counters."""
        # This is called internally when locks change
        pass

    def _get_analytics_data(self) -> dict:
        """Generate analytics data."""
        with self._locks_lock:
            # Count locks per agent
            agent_counts: Dict[str, int] = {}
            for lock in self.locks_by_agent.values():
                agent_counts[lock.agent_name] = agent_counts.get(lock.agent_name, 0) + 1

            most_locked = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Get conflict hotspots
        hotspots = self.pattern_detector.get_hotspots(10)

        # Calculate average lock duration
        avg_duration = 0.0
        if self._lock_durations:
            avg_duration = sum(self._lock_durations) / len(self._lock_durations)

        return ConcurrencyAnalytics(
            total_locks_acquired=len(self.event_manager.lock_history),
            total_locks_released=sum(1 for e in self.event_manager.lock_history if e.event_type in ["released", "overridden"]),
            conflicts_detected=len(self.event_manager.conflict_history),
            deadlocks_resolved=sum(1 for c in self.event_manager.conflict_history if c.auto_resolved),
            most_locked_agents=most_locked,
            conflict_hotspots=[(p.agent_a, p.agent_b, p.conflict_count) for p in hotspots],
            peak_concurrency_time=None,  # TODO: Calculate from time-series data
            avg_lock_duration=avg_duration,
        ).to_dict()

    def register_event_callback(self, callback: Callable):
        """Register a callback for real-time events."""
        self.event_manager.register_callback(callback)

    def unregister_event_callback(self, callback: Callable):
        """Unregister an event callback."""
        self.event_manager.unregister_callback(callback)

    async def start_monitoring(self, interval: float = 5.0):
        """
        Start background deadlock monitoring.

        Args:
            interval: Monitoring interval in seconds
        """
        if self._running:
            return

        self._running = True

        async def monitor_loop():
            while self._running:
                try:
                    deadlocks = await self.detect_deadlocks()

                    if deadlocks and self.enable_auto_resolution:
                        for deadlock in deadlocks:
                            await self.resolve_deadlock(deadlock.cycle)

                except Exception:
                    pass  # Don't let monitoring errors break the loop

                await asyncio.sleep(interval)

        self._monitor_task = asyncio.create_task(monitor_loop())

    async def stop_monitoring(self):
        """Stop background monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass


# ============================================================================
# Singleton Instance
# ============================================================================

_global_manager: Optional[GlobalConcurrencyManager] = None
_manager_lock = threading.Lock()


def get_global_concurrency_manager() -> GlobalConcurrencyManager:
    """Get the singleton GlobalConcurrencyManager instance."""
    global _global_manager

    with _manager_lock:
        if _global_manager is None:
            _global_manager = GlobalConcurrencyManager()
        return _global_manager


def reset_global_concurrency_manager():
    """Reset the singleton instance (mainly for testing)."""
    global _global_manager

    with _manager_lock:
        if _global_manager is not None:
            # Stop monitoring if running
            if hasattr(_global_manager, '_running') and _global_manager._running:
                import asyncio
                try:
                    asyncio.create_task(_global_manager.stop_monitoring())
                except Exception:
                    pass

        _global_manager = None

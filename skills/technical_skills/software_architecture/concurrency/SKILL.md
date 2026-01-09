---
name: software-architecture-concurrency
description: Expertise in designing software systems that execute multiple sequences
  of operations simultaneously, involving synchronization patterns, deadlock avoidance,
  and parallel execution strategies.
metadata:
  skill_id: technical_skills/software_architecture/concurrency
  version: 1.0.0
---

# Software Architecture: Concurrency

Concurrency is the architectural discipline of managing multiple tasks that start, run, and complete in overlapping time periods. Unlike parallelism, which is a hardware execution property, concurrency is a structural property of the software design.

## Core Concepts
- **Memory Models:** Defines how memory operations on one processor are made visible to others. Architects must account for compiler reordering and CPU cache coherence protocols (MESI).
- **Liveness & Safety:** Ensuring a program eventually does something good (liveness) and never does anything bad (safety/consistency).

## Synchronization & Coordination
Architectures must balance the "Cost of Coordination" against data integrity:
- **Pessimistic Locking:** Mutexes and RW-Locks for high-contention, high-integrity writes.
- **Optimistic Concurrency Control (OCC):** Designing for the common case where conflicts are rare, using versions or timestamps.

## Architectural Models
### 1. Actor Model
- **Isolation:** No shared state; communication via immutable messages.
- **Supervision:** Hierarchical management where parents handle failures of child actors (Let-it-crash philosophy).

### 2. Event-Driven & Non-Blocking
- **Reactor Pattern:** Demultiplexing events to synchronous handlers.
- **Proactor Pattern:** Initiating asynchronous operations and handling completion events.

### 3. Shared Memory & Lock-Free
- Use of Atomic primitives (CAS) to build high-performance data structures without thread suspension.
- Addressing the **ABA problem** using tagged pointers or hazard pointers.

## Performance & Scaling
- **Context Switching:** Minimizing the overhead of thread management via work-stealing (e.g., Go's GMP model).
- **Mechanical Sympathy:** Designing concurrency patterns that align with hardware realities, such as avoiding **False Sharing** by padding cache lines.
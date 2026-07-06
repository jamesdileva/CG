# Phase 02 Lessons Learned

- Keep research deterministic where possible; it makes the pipeline easier to debug.
- A no-network fallback keeps the local-first workflow usable, but final scripts should be approved only after real sources are available.
- Route ordering matters in FastAPI. Static paths like `/topic/{topic_id}` must be registered before generic `/{script_id}` paths.

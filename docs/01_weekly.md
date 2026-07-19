### Week 1 — 2026-06-08

**Attended this week's meeting:** Yes

**Progress this week**
- Set up the EVRPTW project structure and organized the repository into reusable modules for instance modeling, distance calculation, random instance generation, feasibility checking, and evaluation.
- Implemented the core data structures for nodes and problem instances, including depot, customers, and charging stations.
- Built a random instance generator and verified that small toy EVRPTW instances can be generated reproducibly using a fixed seed.
- Added distance computation utilities and confirmed that basic geometric routing quantities can be calculated correctly.
- Implemented a feasibility checker and evaluator to support route validation under time-window, battery, and charging-related constraints.
- Wrote and ran unit tests with `pytest`, and confirmed that the current foundation passes all tests successfully.
- Learned the basic structure of the codebase and clarified the role of helper components such as `@property`, `seed`, and instance serialization/IO.

**Challenges & blockers**
- At the start of the week, the repository structure and Python import path setup were confusing, especially when trying to run scripts from the `scripts/` directory.
- The interaction between instance generation, feasibility checking, and evaluation was not immediately clear and required step-by-step debugging.
- I needed additional time to understand how the project modules fit together before I could confidently extend the solver baseline.

**Next steps**
- Continue building the baseline solver and move from simple smoke tests to a more meaningful routing heuristic.
- Add clearer reporting of objective value, feasibility status, runtime, and route output for each experiment.
- Start preparing a more structured weekly workflow so that each milestone can be documented as soon as it is completed.
- Gradually move from the core infrastructure toward a complete EVRPTW solution pipeline.

**Hours spent (optional):**
15

**Links (optional):**
- Core instance and generator modules: `src/instance.py`, `src/distance.py`, `src/generator.py`
- Feasibility and evaluation tools: `src/checker.py`, `src/evaluator.py`
- Smoke test and unit tests: `scripts/`, `tests/`
- Meeting note: `2026-06-08`
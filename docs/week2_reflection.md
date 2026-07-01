# Week 2 Reflection: Baseline Methods Recreation and Preliminary Comparison

## Objective

The objective of Week 2 was to recreate baseline methods for the routing problem, compare their performance on small instances, and document the strengths and limitations of different approaches.

## What I completed

During this week, I focused on building a reproducible baseline pipeline before moving to more advanced methods. The main progress includes:

- building an initial OR-Tools-based VRPTW baseline,
- generating feasible routing solutions on toy/small instances,
- extracting route sequences and arrival times,
- creating route visualizations and arrival-time plots,
- organizing the code structure for later comparison experiments.

At this stage, the work should be considered a **preliminary baseline recreation** rather than a full comparison across all target methods.

## Methods considered

This week mainly focused on the following categories of methods:

### 1. Operations Research / Optimization
This includes solver-based methods such as OR-Tools and, in a broader sense, MILP-style formulations.

In this week's implementation, I used **OR-Tools** as the first practical baseline because it:
- can produce feasible routes quickly,
- supports routing constraints such as time windows,
- is relatively easy to visualize and debug,
- provides a stable starting point for later EVRP-TW extensions.

### 2. Heuristic baseline
A simple heuristic / greedy comparison framework was planned as a lightweight baseline for later testing. This is useful for understanding how much improvement a solver-based method provides over a locally guided method.

### 3. Learning-based / advanced methods
Methods such as **POMO** were reviewed conceptually, but they were not yet implemented in this week's code. These methods require significantly more setup, including training pipelines and reproducible evaluation.

## Current experimental status

At the current stage, I have completed:

- a working OR-Tools baseline,
- route plotting,
- arrival-time visualization,
- preliminary small-instance testing.

I have **not yet completed**:
- a full GA implementation,
- a full POMO reproduction,
- a complete two-scale comparison table with final reported numbers.

Therefore, this week's results should be interpreted as an **initial baseline construction stage** rather than a completed full-method benchmark.

## Preliminary observations

From the current baseline experiments, several observations can already be made:

1. OR-Tools can produce feasible solutions reliably on small instances.
2. The extracted routes and arrival-time plots are useful for checking whether the routing logic is correct.
3. Visualization is especially helpful for identifying whether vehicles are actually used and whether route structures are reasonable.
4. Before extending to EVRP-TW, it is necessary to first verify the correctness of the simpler VRPTW-style pipeline.

## Limitations

The current implementation still has several important limitations:

- It is closer to a **VRPTW baseline** than a full EVRP-TW solver.
- Battery constraints and charging-station decisions are not yet fully integrated.
- A complete comparison against GA or POMO has not yet been completed.
- The current results are still preliminary and mainly intended to validate the baseline pipeline.

## Reflection

This week made it clear that establishing a stable baseline is an important first step. Instead of directly jumping into more advanced algorithms, I first built a solver-based baseline that can generate feasible routes and visual outputs. This is useful because it creates a foundation for later extensions, including battery modeling, charging decisions, and more advanced search or learning-based methods.

Although the comparison across multiple algorithm families is not complete yet, the current work has already clarified the implementation path and reduced uncertainty in the early stage of the project.

## Next steps

The next planned steps are:

- extend the current baseline toward EVRP-TW,
- incorporate battery constraints and charging stations,
- complete a simple heuristic comparison,
- prepare a more systematic comparison across methods and instance sizes,
- continue reviewing GA / ALNS / POMO related papers for possible reproduction choices.

## Related files

- OR-Tools baseline: `src/ortools_vrptw_baseline.py`
- Visualization outputs: `results/`

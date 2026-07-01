# Week 2 Notes: Method Categories and Current Progress

## Overview

This week focused on establishing a first baseline for the routing problem and understanding the differences among several common method categories used in the literature.

The three method categories discussed are:

- POMO
- Genetic Algorithm (GA)
- Operations Research / Optimization methods

At the current stage, the implemented baseline is mainly based on **OR-Tools**, which belongs to the optimization / operations research category.

---

## 1. POMO

### What it is
POMO is a reinforcement-learning-based method for combinatorial optimization problems such as routing. It learns decision policies from data rather than solving each instance only through hand-designed search rules.

### Advantages
- strong learning ability after training,
- suitable for repeated problem distributions,
- widely discussed in neural combinatorial optimization research.

### Challenges
- difficult to reproduce quickly,
- requires training, validation, and testing pipelines,
- needs more engineering effort and usually more computing resources,
- not ideal as the very first baseline when the project pipeline is still being built.

### Current status
I have reviewed POMO conceptually, but I have **not yet reproduced it** in code.

---

## 2. Genetic Algorithm (GA)

### What it is
GA is a metaheuristic that evolves a population of candidate solutions through operators such as selection, crossover, and mutation.

### Advantages
- flexible,
- can be adapted to many routing constraints,
- commonly used in routing literature.

### Challenges
- solution encoding must be designed carefully,
- feasibility repair is often necessary,
- performance can depend strongly on hyperparameters,
- may require significant tuning before fair comparison.

### Current status
A full GA implementation has **not yet been completed**. It remains a candidate direction for later comparison.

---

## 3. Operations Research / Optimization Methods

### What they are
This category includes mathematically structured methods such as MILP formulations and practical solver-based tools such as OR-Tools.

### Advantages
- clear constraint modeling,
- strong feasibility handling,
- interpretable solutions,
- suitable for building a reliable first baseline.

### Challenges
- exact formulations may become slow for larger instances,
- EV-specific constraints can make the model more complex,
- solver behavior may depend on formulation details and parameters.

### Current status
This is the **main method category I implemented this week**. I used OR-Tools to build a VRPTW-style baseline and verified that it can produce feasible routes and useful visualizations.

---

## Why OR-Tools was used first

I chose OR-Tools as the first baseline for the following reasons:

1. it is fast to prototype,
2. it can generate feasible routing solutions,
3. it supports time-window-style constraints,
4. it is easier to debug than advanced learning-based methods,
5. it provides a stable baseline before extending to EVRP-TW.

This makes it a practical first step even though it is not yet the final target method for the full project.

---

## Current progress summary

This week, I completed:

- reading and understanding baseline method categories at a high level,
- implementing an OR-Tools routing baseline,
- testing the code on small instances,
- generating route and arrival-time plots,
- preparing the codebase for later comparison experiments.

This week, I have **not yet completed**:

- full GA reproduction,
- POMO reproduction,
- complete large-scale benchmark comparisons,
- full EVRP-TW battery-and-charging integration.

---

## Preliminary conclusion

At this stage, the most appropriate interpretation is:

- OR-Tools serves as the first reproducible baseline,
- GA and POMO are important comparison targets but are not yet implemented,
- the current work is a foundation-building stage for later, more complete experiments.

---

## Planned next step

The next step is to continue from the current OR-Tools baseline and gradually add:

- battery constraints,
- charging station modeling,
- stronger heuristic / metaheuristic comparison,
- more systematic experiments on different instance sizes.
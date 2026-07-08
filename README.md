# FURP Project Repository

> **Faculty Undergraduate Research Practice (FURP)**  
> Undergraduate Research Group · Faculty of Science and Engineering · University of Nottingham Ningbo China

## Project Info

| Field                        | Your entry                                                                                                                                                                                                         |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Student name(s)              | Jingsheng Zhu                                                                                                                                                                                                      |
| Project title                | Electric Vehicle Routing Problem with Time Windows                                                                                                                                                                 |
| Project tag                  | EVRP-TW                                                                                                                                                                                                            |
| Track                        | Research                                                                                                                                                                                                           |
| Supervising faculty          | Dr Tianxiang Cui                                                                                                                                                                                                   |
| Project lead                 | Fuhua Jia                                                                                                                                                                                                          |
| Team or individual           | Individual                                                                                                                                                                                                         |
| Cited paper being replicated | Keskin, M. and Çatay, B. (2016). *Partial recharge strategies for the electric vehicle routing problem with time windows*. Computers & Operations Research, 65, 111–127. https://doi.org/10.1016/j.cor.2015.07.013 |

**One-line summary:**  
This project studies the Electric Vehicle Routing Problem with Time Windows, focusing on feasible routing under vehicle capacity, customer time-window, and battery/recharging constraints. The current technical plan is to build a reproducible EVRP-TW implementation pipeline and develop an Adaptive Large Neighbourhood Search algorithm, with a later extension using learning-inspired operator selection.

---

## Project Overview

The Electric Vehicle Routing Problem with Time Windows is an extension of the classical Vehicle Routing Problem. In addition to routing vehicles to serve customers, EVRP-TW considers:

- limited vehicle load capacity;
- customer time windows;
- limited battery capacity;
- energy consumption during travel;
- visits to charging stations;
- route feasibility under time and battery constraints.

The goal of this project is to reproduce and understand core EVRP-TW solution methods, then implement and evaluate an ALNS-based heuristic solver.

The project will start from small synthetic instances and gradually move towards benchmark-style instances and more systematic experiments.

---

## Current Research Direction

The current project direction is:

1. Understand VRP, EVRP, EVRP-TW, and related constraints.
2. Build a clean Python codebase for reproducible experiments.
3. Implement an EVRP-TW instance data model.
4. Implement basic feasibility checking for:
   - vehicle capacity;
   - customer service time windows;
   - battery consumption;
   - charging-station visits.
5. Implement simple constructive baseline methods.
6. Develop an Adaptive Large Neighbourhood Search solver.
7. Add a learning-inspired operator selection component as the innovation part.

The planned innovation is to compare standard adaptive operator selection in ALNS with a simple learning-inspired or bandit-style operator selection mechanism.

---

## Current Progress

### Week 1 Foundation

Current work is focused on project foundation and reproducibility.

- [x] Set up Python virtual environment.
- [x] Prepare dependency file `requirements.txt`.
- [x] Update `.gitignore` for Python, data files, and experiment outputs.
- [ ] Define EVRP-TW instance data model.
- [ ] Implement small synthetic EVRP-TW instance generator.
- [ ] Implement JSON input/output format for instances.
- [ ] Add feasibility checker for route constraints.
- [ ] Add initial smoke tests for instance generation and validation.
- [ ] Start weekly research log in `docs/00_weekly.md`.

---

## Technical Roadmap

### Stage 1: Problem Foundation

- Read introductory materials on VRP, EVRP, and EVRP-TW.
- Review the cited EVRP-TW paper and identify the main model assumptions.
- Define the project instance format.
- Implement a small instance generator.
- Implement distance, time, demand, and battery-related utilities.
- Build a feasibility checker.

### Stage 2: Baseline Methods

- Implement simple constructive heuristics.
- Generate feasible initial solutions.
- Establish evaluation metrics:
  - total travel distance;
  - number of vehicles used;
  - feasibility rate;
  - runtime;
  - battery violation and time-window violation checks.

### Stage 3: ALNS Solver

- Implement destroy operators, such as:
  - random customer removal;
  - worst customer removal;
  - related customer removal.
- Implement repair operators, such as:
  - greedy insertion;
  - regret insertion.
- Add an acceptance criterion such as simulated annealing.
- Add adaptive operator weights.
- Compare ALNS performance against simple baselines.

### Stage 4: Learning-Inspired Extension

- Implement a simple learning-inspired operator selection strategy.
- Compare it with random and standard adaptive operator selection.
- Analyze solution quality, convergence behaviour, and runtime.
- Summarize the contribution as the project innovation component.

---

## Repository Structure

This structure follows the FURP project requirement and will be maintained throughout the project.

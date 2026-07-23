# Week 3 Method Decision: GA Baseline and Constraint-Aware Extension

## 1. Purpose of This Document

This document defines the Week 3 experimental direction for the EVRP-TW project.

After reviewing the current GA implementation, the existing GA should **not** be described as a completely basic GA that ignores EVRP-TW constraints. The current implementation already includes several EVRP-related components, including:

1. capacity-based route splitting;
2. simple charging-station insertion;
3. checker-based feasibility evaluation;
4. infeasible-solution penalties.

Therefore, the Week 3 experiment should not be described as:

```text
Basic GA without EVRP-TW constraints
vs
GA with EVRP-TW constraints
```

A more accurate description is:

```text
Existing simple EV-aware GA baseline
vs
Enhanced time-window and energy-aware GA
```

The purpose of Week 3 is to evaluate whether adding more explicit time-window and energy-aware evaluation can improve feasibility and solution quality on EVRP-TW instances.

---

## 2. Current GA Baseline

The current GA baseline uses a permutation-based chromosome.

A chromosome is a sequence of customer IDs. For example:

```text
[4, 2, 6, 1, 5, 3]
```

This chromosome does not directly represent final vehicle routes. It only represents the order in which customers are considered.

The GA then uses a decoder to transform this customer order into vehicle routes.

For example, the chromosome:

```text
[4, 2, 6, 1, 5, 3]
```

may be decoded into:

```text
Route 1: Depot -> 4 -> 2 -> Depot
Route 2: Depot -> 6 -> 1 -> 5 -> Depot
Route 3: Depot -> 3 -> Depot
```

This decoding step is important because EVRP-TW is a multi-route problem. One vehicle route is usually not enough to serve all customers, especially when vehicle capacity, battery range, and time windows are considered.

The current GA includes the following components:

1. initial population generation;
2. nearest-neighbor initial chromosome;
3. depot-distance sorted initial chromosome;
4. random chromosomes;
5. tournament selection;
6. ordered crossover;
7. swap mutation;
8. inversion mutation;
9. elitism;
10. capacity-based route splitting;
11. simple charging-station repair;
12. checker-based feasibility evaluation;
13. penalty for infeasible solutions.

Because of these components, the current GA is better described as:

```text
Simple EV-aware GA baseline
```

rather than:

```text
Pure basic GA
```

---

## 3. What Is Decoding?

In this project, the GA does not directly generate final EVRP-TW routes.

Instead, the GA generates a customer order, and then a decoder converts that order into actual vehicle routes.

For example, suppose we have five customers:

```text
Customers: 1, 2, 3, 4, 5
Depot: 0
```

A GA chromosome may look like this:

```text
[2, 5, 1, 4, 3]
```

This means:

```text
Try to visit customer 2 first,
then customer 5,
then customer 1,
then customer 4,
then customer 3.
```

However, this is not yet a complete EVRP-TW solution. A real EVRP-TW solution needs vehicle routes such as:

```text
Route 1: Depot -> 2 -> 5 -> Depot
Route 2: Depot -> 1 -> 4 -> 3 -> Depot
```

The decoder is the component that performs this transformation:

```text
Customer permutation
        |
        v
Multi-route EVRP-TW solution
```

The decoder decides when to keep adding customers to the current route and when to start a new vehicle route.

For example, if adding the next customer would exceed vehicle capacity, the decoder starts a new route.

Example:

```text
Vehicle capacity = 10

Customer demands:
Customer 2 demand = 4
Customer 5 demand = 5
Customer 1 demand = 3
```

If the current route already contains customers 2 and 5:

```text
Current route load = 4 + 5 = 9
```

Adding customer 1 would make the load:

```text
9 + 3 = 12
```

This exceeds the vehicle capacity of 10, so the decoder starts a new route.

The result becomes:

```text
Route 1: Depot -> 2 -> 5 -> Depot
Route 2: Depot -> 1 -> ...
```

Therefore, decoding is the bridge between the GA's simple customer-order representation and the actual EVRP-TW route solution.

---

## 4. What Constraints Are Already Considered?

### 4.1 Capacity Constraint

The current GA already considers vehicle capacity.

During decoding, the algorithm checks whether adding the next customer would exceed the vehicle capacity.

If the current vehicle cannot serve the next customer without violating capacity, the decoder starts a new vehicle route.

Example:

```text
Vehicle capacity = 10

Current route:
Depot -> Customer A -> Customer B

Current load = 8

Next customer demand = 4
```

If we add the next customer:

```text
8 + 4 = 12
```

This exceeds the vehicle capacity, so the decoder starts a new route:

```text
Route 1: Depot -> Customer A -> Customer B -> Depot
Route 2: Depot -> Next Customer -> ...
```

Therefore, capacity is directly handled in the route construction process.

---

### 4.2 Charging / Battery Constraint

The current GA already includes a simple charging-station repair step.

The idea is:

```text
If the direct distance between two consecutive nodes is too long for the vehicle battery,
try to insert a charging station between them.
```

Example:

```text
Before repair:

Depot -> Customer A -> Customer B -> Depot
```

Suppose the vehicle cannot travel directly from Customer A to Customer B because the distance is longer than the estimated battery range.

Then the repair function tries to insert a charging station:

```text
After repair:

Depot -> Customer A -> Charging Station -> Customer B -> Depot
```

This means the current GA does consider charging stations in a simple way.

However, this charging repair is still limited.

It mainly checks whether one edge can be repaired by inserting one charging station. It does not fully optimize:

1. the vehicle's remaining battery after every move;
2. whether the vehicle should fully or partially recharge;
3. the charging time at the station;
4. how charging affects customer time windows;
5. whether multiple charging stations are needed;
6. whether choosing a farther charging station now may help later.

Therefore, the current charging logic can be described as:

```text
Simple charging-station insertion repair
```

It is not yet a full charging schedule optimization method.

---

### 4.3 Time-Window Constraint

The current GA considers time windows mainly through the feasibility checker.

That means the GA first generates a solution, and then the checker evaluates whether the solution violates any time-window constraints.

A time window usually has the form:

```text
Customer i must be served between earliest_i and latest_i.
```

For example:

```text
Customer 3 time window: [20, 50]
```

This means:

```text
The vehicle should arrive at Customer 3 no earlier than time 20 and no later than time 50.
```

If the vehicle arrives at time 15, it may wait until time 20.

If the vehicle arrives at time 60, it violates the time window.

The current GA can detect such violations through the checker and then penalize the solution.

However, the current decoder does not strongly use time-window information while building routes.

For example, the decoder does not currently say:

```text
If adding this customer will cause late arrival, start a new route.
```

It also does not say:

```text
Customers with earlier deadlines should be considered earlier.
```

Therefore, the current time-window treatment is mainly:

```text
Passive time-window checking
```

rather than:

```text
Active time-window-aware decoding
```

This is an important limitation and a good target for Week 3 improvement.

---

## 5. What Does "Feasible" Mean?

A solution is feasible if it satisfies all required EVRP-TW constraints.

In this project, a feasible solution should satisfy the following conditions.

### 5.1 Every Customer Is Served

Each customer should be visited exactly once.

A solution is infeasible if:

1. a customer is not visited;
2. a customer is visited more than once.

Example of infeasibility:

```text
Customers required: 1, 2, 3, 4

Solution visits:
1, 2, 4
```

Customer 3 is missing, so the solution is infeasible.

---

### 5.2 Vehicle Capacity Is Not Exceeded

For each route, the total demand of customers on that route should not exceed the vehicle capacity.

Example:

```text
Vehicle capacity = 10

Route:
Depot -> Customer 1 -> Customer 2 -> Customer 3 -> Depot

Demands:
Customer 1 = 4
Customer 2 = 5
Customer 3 = 3
```

Total load:

```text
4 + 5 + 3 = 12
```

Since 12 is greater than 10, this route violates the capacity constraint.

Therefore, the solution is infeasible.

---

### 5.3 Battery Constraint Is Satisfied

An electric vehicle has limited battery capacity.

The vehicle should not travel farther than its battery allows unless it recharges at a charging station.

Example:

```text
Battery range = 50

Route segment:
Customer A -> Customer B

Distance from A to B = 70
```

If there is no charging station between A and B, the vehicle cannot complete this segment.

Therefore, the solution is infeasible.

A repaired route may look like this:

```text
Customer A -> Charging Station -> Customer B
```

If both sub-segments are within battery range, the route becomes more likely to be feasible.

---

### 5.4 Time Windows Are Satisfied

Each customer must be served within its time window.

Example:

```text
Customer 5 time window: [30, 80]
```

If the vehicle arrives at time 25, it can wait until time 30.

This is still feasible.

If the vehicle arrives at time 90, it is too late.

This violates the time-window constraint.

Therefore, the solution is infeasible.

---

### 5.5 Routes Start and End at the Depot

Each vehicle route should start from the depot and return to the depot.

Example of a valid route:

```text
Depot -> Customer 1 -> Customer 2 -> Depot
```

Example of an invalid route:

```text
Customer 1 -> Customer 2 -> Depot
```

This route does not start from the depot, so it is infeasible.

---

### 5.6 Fleet Size Is Not Exceeded

If the instance has a limited number of vehicles, the number of routes should not exceed the available vehicle count.

Example:

```text
Available vehicles = 3
```

If the solution contains 5 routes:

```text
Route 1
Route 2
Route 3
Route 4
Route 5
```

Then the solution requires 5 vehicles, but only 3 are available.

Therefore, the solution is infeasible.

---

## 6. Limitation of the Current GA

The current GA is useful as a baseline, but it has several limitations.

First, the charging repair is simple. It can insert a charging station between two nodes, but it does not fully model the battery state across the entire route.

Second, the time-window constraints are mostly handled after a solution has already been generated. The checker can identify violations, but the decoder itself does not actively avoid them.

Third, the fitness function gives penalties to infeasible solutions, but the penalty may not provide enough detailed guidance. For example, the GA may know that a route is infeasible, but it may not know whether the main issue is lateness, battery violation, capacity violation, or missing customers.

Fourth, crossover and mutation are still mostly random. They can create new customer orders that are short in distance but poor in feasibility.

For example, a mutation may move a customer with an early deadline to the end of the route. This may reduce distance in some cases, but it can create a serious time-window violation.

Therefore, Week 3 should focus on making the GA more constraint-aware.

---

## 7. Week 3 Target Method

The Week 3 target method will be an enhanced GA built on top of the existing GA baseline.

The enhanced method will keep the same general GA framework:

1. permutation-based chromosome;
2. population-based search;
3. tournament selection;
4. ordered crossover;
5. mutation;
6. elitism;
7. decoding from customer order to routes.

The main improvement will be in evaluation and constraint awareness.

The enhanced GA may add:

1. stronger time-window penalties;
2. stronger energy-violation penalties;
3. more detailed route simulation;
4. better separation between distance quality and feasibility quality;
5. time-window-aware initial chromosomes;
6. more informative infeasibility measurement.

The goal is not to build a perfect EVRP-TW solver in one week.

The goal is to make the comparison fair, measurable, and scientifically meaningful.

---

## 8. Revised Research Question

The revised research question for Week 3 is:

```text
Does adding more explicit time-window and energy-aware evaluation to an existing simple EV-aware GA improve feasibility and solution quality on EVRP-TW instances of different sizes?
```

This question is more accurate than saying:

```text
Basic GA vs constraint-aware GA
```

because the existing GA already includes capacity splitting and simple charging-station repair.

The correct comparison is:

```text
Simple EV-aware GA baseline
vs
Enhanced time-window and energy-aware GA
```

---

## 9. Comparison Setting

The Week 3 experiment will compare the following two methods.

| Method                      | Description                                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------------------------- |
| Simple EV-aware GA baseline | Current GA implementation with capacity splitting, simple charging repair, and checker-based penalty |
| Enhanced TW-energy-aware GA | New Week 3 version with stronger time-window and energy-aware evaluation                             |

Both methods should be tested using the same experimental setting:

1. same benchmark instances;
2. same random seeds;
3. same customer sizes;
4. same vehicle settings;
5. same population size;
6. same generation count;
7. same feasibility checker;
8. same distance/objective calculation;
9. same runtime measurement;
10. same reporting format.

This makes the comparison fair.

If the enhanced GA uses more computation, this should also be reported. A better feasible rate may come with longer runtime, and this trade-off is important in experimental evaluation.

---

## 10. Expected Result Interpretation

If the enhanced GA has a higher feasible rate, this suggests that explicit time-window and energy-aware evaluation helps guide the search toward valid EVRP-TW solutions.

If the enhanced GA has a shorter average distance among feasible solutions, this suggests that improved constraint handling may also improve route quality.

If the enhanced GA is slower, this is expected because it performs additional constraint-related evaluation.

If both methods fail on large instances, this should not be hidden. Instead, the report should analyze why the failure happens.

Possible reasons include:

1. large customer size;
2. strict time windows;
3. limited battery capacity;
4. insufficient charging-station repair;
5. insufficient number of GA generations;
6. small population size;
7. weak mutation/crossover strategy;
8. limited fleet size;
9. checker being strict;
10. route decoder not being strong enough.

Failure analysis is still valuable because it shows the limitation of the current method and motivates future improvement.

---

## 11. Final Decision

For Week 3, the existing GA will be kept as the baseline.

The original GA code should not be overwritten because it is needed for comparison.

A new enhanced GA file will be added for the Week 3 target method.

The new method can reuse components from the existing GA, such as:

1. chromosome representation;
2. crossover;
3. mutation;
4. distance calculation;
5. checker calls;
6. decoding utilities.

This design keeps the experiment clean:

```text
Old method stays unchanged as baseline.
New method is added as target.
Both methods are compared under the same experimental runner.
```

Therefore, the Week 3 implementation plan is:

```text
Step 1: Define the baseline and target method clearly.
Step 2: Add an enhanced TW-energy-aware GA implementation.
Step 3: Build a unified experiment runner.
Step 4: Compare feasibility, distance, and runtime.
Step 5: Write the Week 3 evaluation report.
```

---

## 12. Summary

The current GA already has basic EV-aware features, including capacity splitting and simple charging-station insertion.

However, its time-window and energy handling are still limited.

Week 3 will therefore focus on evaluating whether a more explicit time-window and energy-aware GA can improve solution feasibility and quality.

The key idea is not to replace the whole GA, but to enhance the evaluation and constraint-awareness while keeping the same general genetic algorithm framework.

This makes the Week 3 experiment realistic, fair, and suitable for report writing.
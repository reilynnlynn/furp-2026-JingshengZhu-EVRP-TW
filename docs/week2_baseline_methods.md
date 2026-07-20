# Week 2 Baseline Methods Recreation and Comparison

## 1. Objective of Week 2

The objective of Week 2 is to recreate and compare several baseline methods for the Electric Vehicle Routing Problem with Time Windows (EVRP-TW).

According to the Week 2 lab requirement, the main task is:

> Review some papers or representative methods, recreate the proposed methods at a simplified baseline level, and write a short overview/conclusion comparing the results and methodologies.

In this project, the following baseline methods were implemented and compared:

```text
1. random
2. nearest_neighbor
3. pomo_style
4. ga_style
5. or_sweep
```

The goal of this week is not to produce the best possible EVRP-TW solver. Instead, the goal is to build a consistent experimental framework where different baseline ideas can be tested under the same instance generator, decoder, feasibility checker, and evaluator.

---

## 2. Overall Framework

The Week 2 framework follows the pipeline below:

```text
Generate EVRP-TW instance
        ↓
Baseline method generates a customer visiting order
        ↓
Shared multi-route decoder converts the order into multiple vehicle routes
        ↓
Feasibility checker checks whether the solution satisfies problem constraints
        ↓
Evaluator computes objective values and statistics
        ↓
Comparison table is generated for 50 / 100 / 200 customers
```

The key design decision is to separate the problem into two parts:

```text
Method-specific part:
    Generate a customer visiting order.

Shared part:
    Decode the order into multiple EVRP-TW routes and evaluate the solution.
```

This makes the comparison fairer because all methods are evaluated using the same decoder, checker, and evaluator.

---

## 3. Why a Shared Multi-route Decoder Is Needed

EVRP-TW is a vehicle routing problem, not a traveling salesman problem.

A traveling salesman problem usually has one route:

```text
depot -> customer 1 -> customer 2 -> ... -> customer n -> depot
```

However, a vehicle routing problem usually has multiple routes:

```text
route 1: depot -> customer a -> customer b -> depot
route 2: depot -> customer c -> customer d -> depot
route 3: depot -> customer e -> customer f -> depot
```

Therefore, if a baseline only outputs one long route, the problem is reduced to a TSP-like setting and does not properly represent VRP or EVRP-TW.

To solve this issue, Week 2 introduces a shared multi-route decoder. Each baseline method first generates a permutation of customers, and the decoder splits this permutation into multiple vehicle routes according to the problem constraints.

For example, if a method generates the following customer order:

```text
[5, 2, 8, 1, 7, 3, 4, 6]
```

The decoder may convert it into multiple routes:

```text
Route 1: depot -> 5 -> 2 -> 8 -> depot
Route 2: depot -> 1 -> 7 -> depot
Route 3: depot -> 3 -> 4 -> 6 -> depot
```

This allows all baselines to be compared as multi-vehicle routing methods.

---

## 4. Baseline Methods

### 4.1 Random Baseline

The `random` baseline is the simplest baseline method.

It randomly shuffles all customer nodes and sends the resulting customer order to the shared multi-route decoder.

Example:

```text
Original customers:
[1, 2, 3, 4, 5, 6]

Random order:
[4, 1, 6, 2, 5, 3]
```

Then the shared decoder converts this order into multiple vehicle routes.

The random baseline is not expected to perform well. It is included because it provides a lower-bound reference point. If a more advanced method performs similarly to random, then the method may not be using useful routing structure.

Advantages:

```text
- Very easy to implement.
- Very fast.
- Useful as a sanity-check baseline.
```

Disadvantages:

```text
- Does not use distance information.
- Does not use time-window information during order construction.
- Usually produces long and inefficient routes.
```

---

### 4.2 Nearest-Neighbor Baseline

The `nearest_neighbor` baseline is a greedy constructive heuristic.

The main idea is:

```text
Starting from the depot, repeatedly visit the closest unvisited customer.
```

The algorithm works as follows:

```text
1. Start from the depot.
2. Find the closest unvisited customer.
3. Move to that customer.
4. From the current customer, find the next closest unvisited customer.
5. Repeat until all customers are ordered.
6. Send the customer order to the shared multi-route decoder.
```

Example:

```text
Current position: depot
Unvisited customers: A, B, C, D

If customer A is closest to the depot, visit A first.
Then from A, choose the closest unvisited customer again.
```

Advantages:

```text
- Simple and fast.
- Easy to interpret.
- Uses distance information.
- Often a strong simple baseline for routing problems.
```

Disadvantages:

```text
- Greedy and local.
- Does not guarantee global optimality.
- Early decisions may cause inefficient later routes.
- Does not directly optimize charging station usage or time windows during order construction.
```

In this project, nearest-neighbor is included because greedy heuristics are commonly used baseline methods in vehicle routing problems.

---

### 4.3 POMO-style Baseline

The `pomo_style` baseline recreates the high-level idea of the POMO approach.

POMO stands for:

```text
Policy Optimization with Multiple Optima
```

The original POMO method is a neural combinatorial optimization approach. It is often used for routing problems such as TSP and CVRP.

The key idea of POMO is:

```text
Do not construct only one solution.
Instead, start from multiple different points or perform multiple rollouts,
generate multiple candidate solutions, and select the best one.
```

#### Original POMO Idea

In routing problems, the starting point or construction trajectory can strongly affect the final solution quality.

For example, even if two routes visit the same customers, different construction orders may lead to different route structures:

```text
Candidate order 1:
[1, 2, 3, 4, 5]

Candidate order 2:
[3, 4, 5, 1, 2]

Candidate order 3:
[5, 1, 4, 2, 3]
```

POMO tries to use multiple starting points or multiple trajectories so that the algorithm has more chances to find a good solution.

#### Simplified POMO-style Implementation in This Project

This Week 2 implementation does not reproduce the full neural network training pipeline of POMO.

A full POMO implementation would require:

```text
- A neural encoder-decoder model.
- Reinforcement learning training.
- Policy gradient optimization.
- Large training datasets.
- GPU training time.
- Model checkpointing and testing.
```

Instead, this project implements a lightweight POMO-style baseline.

The simplified idea is:

```text
1. Generate multiple candidate customer orders using different starting points.
2. Decode each customer order into a multi-route EVRP-TW solution.
3. Evaluate each decoded solution.
4. Keep the solution with the best objective value.
```

Pseudo-code:

```text
best_solution = None
best_distance = infinity

for start_customer in candidate_start_customers:
    order = construct_customer_order_from_start(start_customer)
    solution = shared_multi_route_decoder(order)
    distance = evaluate(solution)

    if distance < best_distance:
        best_solution = solution
        best_distance = distance

return best_solution
```

This captures the main methodological idea of POMO:

```text
Explore multiple construction trajectories instead of relying on one deterministic route construction.
```

#### Strengths of the POMO-style Baseline

```text
- More exploratory than single-start greedy construction.
- Can generate several candidate solutions and select the best one.
- Often more stable on larger instances.
- Still relatively simple compared with full neural POMO.
```

#### Weaknesses of the POMO-style Baseline

```text
- It is not a full neural POMO implementation.
- It does not include reinforcement learning training.
- The quality depends on how candidate starting points are selected.
- It can be slower than nearest-neighbor because multiple candidates are evaluated.
```

#### Interpretation in This Project

In the current experiment, `pomo_style` performs particularly well on the 200-customer cases. This suggests that multi-start construction can be helpful when the instance size becomes larger.

However, the result should be interpreted as a simplified recreation of the POMO idea, not as a direct reproduction of the original neural POMO paper.

---

### 4.4 GA-style Baseline

The `ga_style` baseline recreates the idea of a genetic algorithm for EVRP-TW.

GA stands for:

```text
Genetic Algorithm
```

A genetic algorithm is an evolutionary search method inspired by natural selection.

The general process is:

```text
population
    ↓
selection
    ↓
crossover
    ↓
mutation
    ↓
survival / replacement
    ↓
new population
```

This process is repeated for multiple generations.

#### Representation

In this project, each individual in the genetic algorithm is a customer permutation.

Example:

```text
[4, 2, 8, 1, 5, 7, 3, 6]
```

This permutation is not yet a complete EVRP-TW solution. It only represents the order in which customers should be considered.

The shared multi-route decoder then converts the permutation into multiple vehicle routes:

```text
Route 1: depot -> 4 -> 2 -> 8 -> depot
Route 2: depot -> 1 -> 5 -> 7 -> depot
Route 3: depot -> 3 -> 6 -> depot
```

#### Fitness Evaluation

Each individual is evaluated by:

```text
1. Decoding the permutation into vehicle routes.
2. Checking whether the solution is feasible.
3. Computing the total travel distance.
4. Assigning a fitness value.
```

A shorter total distance means a better individual.

A simple fitness function can be:

```text
fitness = -total_distance
```

or:

```text
fitness = 1 / total_distance
```

If a solution is infeasible, a penalty can be added.

#### Selection

Selection chooses better individuals as parents.

The idea is:

```text
Good solutions should have a higher probability of producing children.
```

Common selection strategies include:

```text
- tournament selection
- roulette-wheel selection
- rank-based selection
```

In a simplified baseline, tournament selection is often used because it is easy and stable.

#### Crossover

Crossover combines two parent permutations to generate a new child permutation.

For routing problems, crossover must preserve the permutation property:

```text
Each customer should appear exactly once.
```

Example:

```text
Parent 1:
[1, 2, 3, 4, 5, 6]

Parent 2:
[4, 6, 2, 1, 5, 3]
```

A crossover operator may copy part of Parent 1 and fill the missing customers using the order from Parent 2.

Example child:

```text
[1, 2, 3, 4, 6, 5]
```

The exact child depends on the crossover rule.

#### Mutation

Mutation randomly changes a permutation to maintain diversity.

A simple mutation is swap mutation:

```text
Before mutation:
[1, 2, 3, 4, 5, 6]

Swap positions of 2 and 5:

After mutation:
[1, 5, 3, 4, 2, 6]
```

Mutation prevents the population from becoming too similar too early.

#### Simplified GA-style Algorithm

Pseudo-code:

```text
Initialize a population of random customer permutations

for generation in range(number_of_generations):
    Evaluate every individual using decoder and evaluator
    Select good individuals as parents
    Apply crossover to generate children
    Apply mutation to some children
    Decode and evaluate children
    Keep the best individuals for the next generation

Return the best decoded solution
```

#### Strengths of the GA-style Baseline

```text
- Can explore a larger solution space than greedy methods.
- Uses population-based search.
- Crossover and mutation can discover new route structures.
- Can improve over generations.
```

#### Weaknesses of the GA-style Baseline

```text
- Slower than greedy methods.
- Requires parameter tuning, such as population size and mutation rate.
- May not outperform simpler methods if the search budget is small.
- The decoded solution quality depends strongly on the shared decoder.
```

#### Interpretation in This Project

In the current experiment, the GA-style baseline performs better than random and OR-sweep, and it is competitive with nearest-neighbor and POMO-style in some cases.

However, it is usually slower because many candidate permutations must be decoded and evaluated.

This is expected because GA trades runtime for search ability.

---

### 4.5 OR-style Sweep Baseline

The `or_sweep` baseline is inspired by classical operations research heuristics.

The sweep algorithm is a traditional VRP construction heuristic.

The main idea is:

```text
Sort customers by their polar angle around the depot.
Then group nearby angular customers into routes.
```

#### Geometric Intuition

Suppose the depot is at the center. Each customer has a location around the depot.

The sweep algorithm converts each customer location into an angle:

```text
angle = atan2(customer_y - depot_y, customer_x - depot_x)
```

Then customers are sorted by angle:

```text
customer 3 -> customer 8 -> customer 1 -> customer 5 -> customer 2 -> ...
```

The algorithm sweeps around the depot like a rotating ray and groups customers in that order.

#### Why Sweep Can Be Used for VRP

Customers with similar angles are often geographically close in the same direction from the depot.

Therefore, assigning them to the same route may reduce unnecessary crossing routes.

Example:

```text
Customers in the northeast area may form one route.
Customers in the southwest area may form another route.
```

#### Simplified OR-sweep Algorithm

Pseudo-code:

```text
1. Compute the polar angle of each customer relative to the depot.
2. Sort customers by angle.
3. Send the sorted customer order to the shared multi-route decoder.
4. Evaluate the decoded multi-route solution.
```

#### Strengths of the OR-sweep Baseline

```text
- Very interpretable.
- Based on classical VRP heuristic ideas.
- Uses spatial/geometric information.
- Fast and deterministic.
```

#### Weaknesses of the OR-sweep Baseline

```text
- Only uses angular information.
- Does not directly minimize local travel distance.
- May perform poorly if customers are not radially clustered.
- Does not directly optimize time windows or charging decisions during ordering.
```

#### Interpretation in This Project

In the current experiment, OR-sweep is feasible but has longer average distances than nearest-neighbor, POMO-style, and GA-style.

This suggests that although geometric grouping is useful, angle-based ordering alone may not be enough for these random EVRP-TW instances.

---

## 5. What Does "Feasible" Mean?

In EVRP-TW, a solution is feasible if it satisfies the problem constraints.

A feasible solution should usually satisfy the following conditions:

```text
1. Every customer is visited exactly once.
2. No customer is missed.
3. No customer is visited more than once.
4. Each route starts from the depot.
5. Each route ends at the depot.
6. Vehicle capacity is not exceeded.
7. Vehicle battery constraints are satisfied.
8. Time-window constraints are satisfied.
9. The number of used vehicles or routes is allowed.
10. The vehicle can return to the depot safely.
```

In the experiment table, the column `feasible_rate` means:

```text
feasible_rate = number_of_feasible_runs / total_number_of_runs
```

For example:

```text
feasible_rate = 1.0
```

means all tested runs are feasible.

```text
feasible_rate = 0.8
```

means 80% of tested runs are feasible.

A method with a high feasible rate is reliable because it can generate valid EVRP-TW solutions more often.

However, feasibility alone is not enough. Among feasible solutions, we also care about:

```text
- total distance
- number of routes
- runtime
```

A feasible but very long route solution is valid but not necessarily good.

---

## 6. Current Treatment of EVRP-TW Constraints

This project currently uses a shared decoder and a solution checker to evaluate whether solutions satisfy the EVRP-TW constraints.

The main constraints are handled in the following way.

### 6.1 Multiple Routes

Multiple routes are considered.

The shared decoder converts a single customer visiting order into multiple vehicle routes.

This fixes the previous issue where some methods produced only one route.

### 6.2 Vehicle Capacity

Vehicle capacity is considered during decoding and/or feasibility checking.

If adding a customer would exceed vehicle capacity, the decoder should start a new route.

This is a standard VRP constraint.

### 6.3 Time Windows

Time-window constraints are part of EVRP-TW.

In a full EVRP-TW setting, each customer has a time window:

```text
ready_time <= arrival_time <= due_time
```

If a vehicle arrives early, it can wait.

If a vehicle arrives after the due time, the route becomes infeasible.

The feasibility checker should verify whether the arrival time at each customer satisfies the time window.

In the current Week 2 framework, time windows are included at the feasibility-checking level if they are implemented in `checker.py`.

However, the baseline construction methods do not explicitly optimize time windows when generating customer orders.

That means:

```text
- Time windows can be checked.
- But the methods are not yet strongly time-window-aware.
```

Improving time-window-aware construction is a good direction for Week 3.

### 6.4 Battery Constraint

Battery constraint is a core part of EVRP.

The vehicle consumes energy while traveling. A route is battery-feasible if the vehicle can travel along the route without running out of battery.

The basic energy calculation is usually:

```text
energy_consumed = distance * energy_consumption_rate
```

A route should satisfy:

```text
remaining_battery >= required_energy
```

for every travel segment.

The feasibility checker should verify the battery constraint.

In the current Week 2 implementation, the solution is checked for battery feasibility if battery checking is implemented in `checker.py`.

However, the current baseline methods mainly construct customer orders and routes. They do not yet perform advanced charging-station insertion.

Therefore, the current battery treatment is baseline-level:

```text
- Battery feasibility can be checked.
- Routes can be split to avoid overly long routes.
- But charging station insertion is not yet deeply optimized.
```

### 6.5 Charging Stations

Charging stations are an important part of EVRP.

A full EVRP solution may include charging station visits:

```text
depot -> customer 1 -> charging station -> customer 2 -> depot
```

Charging station insertion becomes necessary when the vehicle cannot complete a route with its current battery.

In the current Week 2 implementation, charging stations are not the main focus of the baseline recreation. The framework may include station nodes in the instance, but the baseline methods do not yet perform advanced charging station selection or insertion.

This means the current Week 2 result should be described carefully:

```text
The Week 2 baselines mainly compare customer-order construction strategies under a shared EVRP-TW decoding and checking framework. Charging station insertion is not yet fully optimized and should be improved in the next stage.
```

A stronger Week 3 improvement would be:

```text
1. Detect when a vehicle cannot reach the next customer or return to the depot.
2. Search for reachable charging stations.
3. Insert the best charging station into the route.
4. Update vehicle battery and time.
5. Continue decoding the route.
```

---

## 7. Experimental Setup

The experiments compare the baseline methods on randomly generated EVRP-TW instances.

The tested customer sizes are:

```text
50 customers
100 customers
200 customers
```

The tested random seeds are:

```text
1, 2, 3, 4, 5
```

The compared methods are:

```text
random
nearest_neighbor
pomo_style
ga_style
or_sweep
```

For each method and each instance size, the experiment reports:

```text
- feasible_rate
- average assigned customers
- average unassigned customers
- average number of routes
- average total distance
- average runtime
```

---

## 8. Experimental Results

The experiment produced the following summary results.

```md
| Method           | Size | Feasible Rate | Avg Assigned | Avg Unassigned | Avg Routes | Avg Distance | Avg Runtime |
| ---------------- | ---: | ------------: | -----------: | -------------: | ---------: | -----------: | ----------: |
| random           |   50 |         1.000 |         50.0 |            0.0 |       5.00 |      3663.45 |      0.0002 |
| random           |  100 |         1.000 |        100.0 |            0.0 |      10.00 |      6909.58 |      0.0004 |
| random           |  200 |         1.000 |        200.0 |            0.0 |      20.00 |     10756.55 |      0.0008 |
| nearest_neighbor |   50 |         1.000 |         50.0 |            0.0 |       5.00 |      1466.20 |      0.0017 |
| nearest_neighbor |  100 |         1.000 |        100.0 |            0.0 |      10.00 |      1785.53 |      0.0064 |
| nearest_neighbor |  200 |         1.000 |        200.0 |            0.0 |      20.00 |      1997.26 |      0.0259 |
| pomo_style       |   50 |         1.000 |         50.0 |            0.0 |       5.00 |      1493.59 |      0.0041 |
| pomo_style       |  100 |         1.000 |        100.0 |            0.0 |      10.00 |      1785.53 |      0.0153 |
| pomo_style       |  200 |         1.000 |        200.0 |            0.0 |      20.00 |      1887.06 |      0.0676 |
| ga_style         |   50 |         1.000 |         50.0 |            0.0 |       5.00 |      1513.23 |      0.0177 |
| ga_style         |  100 |         1.000 |        100.0 |            0.0 |      10.00 |      1852.58 |      0.0377 |
| ga_style         |  200 |         1.000 |        200.0 |            0.0 |      20.00 |      1944.54 |      0.0763 |
| or_sweep         |   50 |         1.000 |         50.0 |            0.0 |       5.00 |      2217.92 |      0.0001 |
| or_sweep         |  100 |         1.000 |        100.0 |            0.0 |      10.00 |      2748.99 |      0.0001 |
| or_sweep         |  200 |         1.000 |        200.0 |            0.0 |      20.00 |      3719.14 |      0.0003 |
```

---

## 9. Result Analysis

### 9.1 Feasibility

All methods achieved:

```text
feasible_rate = 1.000
```

for 50, 100, and 200 customers.

This means that all tested runs produced feasible solutions according to the current checker and decoder.

This is a positive result because it shows the shared decoder can construct valid multi-route solutions for all tested methods and instance sizes.

However, this result should be interpreted carefully. Since the current baselines are mainly focused on customer ordering and route splitting, the feasibility result depends heavily on the decoder and checker. More difficult time-window and charging-station logic should be further tested in the next stage.

### 9.2 Distance Comparison

The random baseline has the largest average distance.

This is expected because it does not use distance or geometry when creating the customer order.

For 200 customers:

```text
random distance: 10756.55
nearest_neighbor distance: 1997.26
pomo_style distance: 1887.06
ga_style distance: 1944.54
or_sweep distance: 3719.14
```

This shows that structured construction methods produce much shorter routes than random ordering.

Among the structured methods, `pomo_style`, `nearest_neighbor`, and `ga_style` perform relatively well.

### 9.3 Runtime Comparison

The fastest methods are:

```text
random
or_sweep
nearest_neighbor
```

The slower methods are:

```text
pomo_style
ga_style
```

This is expected because POMO-style evaluates multiple candidate constructions, and GA-style evaluates many individuals over multiple generations.

Therefore, there is a trade-off:

```text
Better search quality usually requires more runtime.
```

### 9.4 Method Ranking by Distance

For the 200-customer case, the ranking by average distance is approximately:

```text
1. pomo_style
2. ga_style
3. nearest_neighbor
4. or_sweep
5. random
```

This suggests that multi-start and evolutionary search strategies can be useful for larger routing instances.

However, nearest-neighbor remains very competitive because it is simple, fast, and directly uses distance information.

---

## 10. Methodology Comparison and Conclusion

The Week 2 implementation compares several baseline ideas under the same EVRP-TW evaluation framework.

The main methodological comparison is:

```md
| Method           | Main Idea                                              | Strength                                 | Weakness                                             |
| ---------------- | ------------------------------------------------------ | ---------------------------------------- | ---------------------------------------------------- |
| random           | Randomly shuffle customers                             | Very simple and fast                     | No routing intelligence                              |
| nearest_neighbor | Always visit the closest unvisited customer            | Fast and strong simple baseline          | Greedy and local                                     |
| pomo_style       | Generate multiple candidate routes and select the best | More exploration, strong on larger cases | Not full neural POMO, slower than greedy             |
| ga_style         | Use population-based evolutionary search               | Can explore many permutations            | Slower and parameter-sensitive                       |
| or_sweep         | Sort customers geometrically by polar angle            | Classical and interpretable              | May produce long routes if angle order is not enough |
```

The results show that structured baselines significantly outperform random ordering.

The POMO-style method performs best on the largest tested instances, suggesting that multi-start construction can improve solution quality.

The GA-style method also performs competitively because it searches over multiple customer permutations.

Nearest-neighbor is still an important baseline because it is simple, fast, and effective.

OR-sweep provides a classical operations research comparison point, but its distance is larger in these random instances.

Overall, Week 2 establishes a baseline comparison framework for EVRP-TW. The current implementation focuses on comparing customer-order construction methods using a shared multi-route decoder and feasibility checker.

The next improvement should focus on making the decoder more EVRP-specific, especially by improving:

```text
1. charging station insertion,
2. battery-aware route construction,
3. time-window-aware customer ordering,
4. stronger infeasibility handling,
5. more realistic benchmark instances.
```

---

## 11. Limitations

The current Week 2 implementation has the following limitations:

```text
1. The POMO-style method is a lightweight recreation of the multi-start idea, not a full neural POMO implementation.
2. The GA-style method is a simplified evolutionary baseline and may require more parameter tuning.
3. The OR-sweep method only uses geometric angle information.
4. Charging station insertion is not yet deeply optimized.
5. Time windows are checked if implemented in the checker, but the baselines are not strongly time-window-aware during construction.
6. The experimental instances are randomly generated, so results may differ on standard benchmark datasets.
```

These limitations are acceptable for Week 2 because the goal is baseline recreation and comparison. They also define the direction for Week 3.

---

## 12. Next Steps

The next step is to improve the EVRP-TW-specific decoder.

Important future work includes:

```text
1. Add explicit charging station insertion.
2. Choose charging stations based on distance, battery feasibility, and time-window impact.
3. Make route construction time-window-aware.
4. Penalize or repair infeasible solutions.
5. Compare methods on harder instances.
6. Add more detailed constraint violation statistics.
```

This will make the project closer to a full EVRP-TW solver instead of only a customer-order baseline comparison framework.
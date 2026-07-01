### Week 2 — 2026-06-15

**Attended this week's meeting:** No, because I initially thought I had acute gastroenteritis and threw up twice. Later I went to the hospital and found out it was appendicitis, so I was hospitalized for surgery.

**Progress this week**
- Started building an OR-Tools VRPTW baseline and ran an initial feasible routing example.
- Began learning the basic structure of OR-Tools, including the data model, routing manager, routing model, callback functions, and dimensions.
- Developed a preliminary understanding of how time windows are modeled in OR-Tools and how solver outputs can be extracted into routes.
- Added simple visualization for the baseline, including a route map and an arrival-time plot, to help inspect the solution.
- Started extending my own Python prototype from VRPTW toward EVRP-TW by adding battery-capacity and energy-consumption constraints.
- Made an initial attempt to include charging stations with a simplified full-recharge rule in a toy instance.
- Conducted small smoke tests to check whether the battery and charging logic affects route feasibility as expected.

**Challenges & blockers**
- My understanding of OR-Tools is still at an early stage, especially for dimensions, cumulative variables, and internal solver indexing.
- The current OR-Tools baseline is still basic and has not yet been systematically compared with another baseline method.
- My EVRP-TW prototype is still a simplified early version and does not yet include all required EVRP-TW elements in one complete framework.
- I am still deciding whether to continue mainly with OR-Tools, with my own routing logic, or with a combination of both approaches.

**Next steps**
- Continue improving the OR-Tools VRPTW baseline and make the code structure clearer.
- Read more reference implementations and examples to better understand how baseline recreation should be done.
- Try a small baseline comparison by modifying one component or one setting in the current OR-Tools workflow.
- Continue extending the EVRP-TW prototype and gradually integrate more constraints into a cleaner implementation.
- Improve the current visualizations so that the routing results can be presented more clearly in meetings.

**Hours spent (optional):**
10

**Links (optional):**
OR-Tools baseline: `src/ortools_vrptw_baseline.py`  
OR-Tools visualization: `src/ortools_vrptw_benchmark.py`  
OR-Tools with two more vehicles:`src/ortools_vrptw_two_vehicles.py`  
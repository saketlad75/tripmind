# Performance Optimization: Parallel Agent Execution

## Overview

The TripMind orchestrator has been optimized to run agents in parallel where possible, significantly reducing latency.

## Before Optimization (Sequential Execution)

```
StayAgent → RestaurantAgent → TravelAgent → ExperienceAgent → BudgetAgent → PlannerAgent
```

**Total Time**: `T(Stay) + T(Restaurant) + T(Travel) + T(Experience) + T(Budget) + T(Planner)`

If each agent takes ~30 seconds:
- Total: ~180 seconds (3 minutes)

## After Optimization (Parallel Execution)

```
StayAgent → [RestaurantAgent, TravelAgent, ExperienceAgent in parallel] → BudgetAgent → PlannerAgent
```

**Total Time**: `T(Stay) + max(T(Restaurant), T(Travel), T(Experience)) + T(Budget) + T(Planner)`

If each agent takes ~30 seconds:
- Total: ~120 seconds (2 minutes)
- **40% faster!**

## Agent Dependencies

### Can Run in Parallel
- **RestaurantAgent** - Only needs `stay_results`
- **TravelAgent** - Only needs `stay_results`
- **ExperienceAgent** - Only needs `stay_results`

All three agents can run simultaneously after StayAgent completes.

### Must Run Sequentially
- **StayAgent** - Must run first (no dependencies)
- **BudgetAgent** - Needs results from RestaurantAgent, TravelAgent, and ExperienceAgent
- **PlannerAgent** - Needs results from all previous agents

## Implementation Details

### Parallel Execution Node

The `_parallel_agents_node` method uses `asyncio.gather()` to run three agents concurrently:

```python
results = await asyncio.gather(
    run_restaurant(),
    run_travel(),
    run_experience(),
    return_exceptions=True
)
```

### Error Handling

If any agent fails, the system:
1. Logs the error
2. Returns empty results for that agent
3. Continues with the remaining agents
4. Allows the workflow to proceed

## Expected Performance Improvements

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| All agents ~30s each | 180s | 120s | **33% faster** |
| Restaurant slow (60s), others 30s | 210s | 150s | **29% faster** |
| All agents ~20s each | 120s | 80s | **33% faster** |

## Monitoring

The logs will show:
```
⚡ [2-4/6] Running agents in parallel: RestaurantAgent, TravelAgent, ExperienceAgent...
   🍽️  RestaurantAgent: Finding restaurants...
   ✈️  TravelAgent: Finding transportation options...
   🎯 ExperienceAgent: Finding local activities...
   ✅ RestaurantAgent: Found X restaurants
   ✅ TravelAgent: Found X transportation options
   ✅ ExperienceAgent: Found X experiences
✅ All parallel agents completed!
```

## Future Optimization Opportunities

1. **BudgetAgent and PlannerAgent**: Could potentially run in parallel if PlannerAgent doesn't need budget details
2. **StayAgent sub-tasks**: If StayAgent has multiple search operations, they could be parallelized
3. **Caching**: Cache results from previous requests to avoid redundant API calls

## Testing

To verify the optimization is working:

1. Check the logs for parallel execution messages
2. Compare total execution time before and after
3. Monitor that all three agents start simultaneously after StayAgent completes


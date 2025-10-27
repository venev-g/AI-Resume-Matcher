---
applyTo: "backend/**/*graph*.py"
---

# LangGraph Orchestration Instructions

## LangGraph 1.0 Architecture
Using LangGraph 1.0 (Oct 2025 GA release) for durable state management and agent orchestration.

## Graph Structure

### State Definition
```python
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

class GraphState(TypedDict):
    # Define all state fields with types
    jd_text: str
    resume_files: List[str]
    jd_data: Dict
    resume_data: List[Dict]
    # ... other state fields
```

### Graph Building Pattern
```python
def _build_graph(self) -> StateGraph:
    workflow = StateGraph(GraphState)
    
    # Add nodes (agent methods)
    workflow.add_node("node_name", self.node_method)
    
    # Set entry point
    workflow.set_entry_point("first_node")
    
    # Define edges (linear or conditional)
    workflow.add_edge("node1", "node2")
    workflow.add_conditional_edges(
        "node2",
        self.should_continue,
        {
            "continue": "node3",
            "end": END
        }
    )
    
    return workflow.compile()
```

### Node Implementation
```python
async def node_method(self, state: GraphState) -> GraphState:
    \"\"\"Process state and return updated state.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated graph state
    \"\"\"
    # Extract data from state
    input_data = state["field_name"]
    
    # Process with agent
    result = await self.agent.process(input_data)
    
    # Update state
    state["output_field"] = result
    
    return state
```

## Workflow Best Practices

### Sequential Processing
For the resume matcher, use **linear workflow**:
1. extract_jd → 2. analyze_resumes → 3. generate_embeddings → 4. evaluate_matches → 5. recommend_skills

### State Management
- **Immutable updates**: Create new dicts, don't mutate
- **Type safety**: Ensure all fields match GraphState
- **Error handling**: Wrap node logic in try-except
- **Logging**: Log state transitions for debugging

### Execution
```python
async def execute(self, inputs: Dict) -> Dict:
    # Initialize state
    initial_state = GraphState(
        jd_text=inputs["jd_text"],
        resume_files=inputs["resume_files"],
        # ... initialize all required fields
    )
    
    # Execute graph asynchronously
    result = await self.graph.ainvoke(initial_state)
    
    # Extract final output
    return result["final_output"]
```

### Checkpointing (Optional)
For long-running workflows, implement checkpointing:
```python
from langgraph.checkpoint import MemorySaver

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

### Error Recovery
```python
async def error_handling_node(self, state: GraphState) -> GraphState:
    try:
        # Node logic
        result = await process()
        state["result"] = result
    except Exception as e:
        logger.error(f"Node failed: {e}")
        state["error"] = str(e)
        state["failed_node"] = "node_name"
    return state
```

## Integration with Services
- Initialize **Pinecone** and **MongoDB** clients in __init__
- Store results in **MongoDB** after final node
- Upsert embeddings to **Pinecone** in embedding node
- Clean up **temporary files** in final node

## Performance Optimization
- Use **asyncio.gather()** for parallel processing (multiple resumes)
- Implement **batching** for embedding generation
- Add **timeouts** to prevent infinite loops
- Cache **intermediate results** when possible
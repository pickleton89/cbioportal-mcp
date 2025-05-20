---
trigger: manual
---

# Graphiti MCP Agent Memory Rules (Condensed)

**Purpose:**  
Maintain persistent, context-aware memory for AI assistants via Graphiti's knowledge graph.

---

## 1. Key Concepts

- **Episode:** A stored item (text, message, or JSON) representing facts, user input, or structured data.
- **Entity:** A node in the graph, e.g., Preference, Procedure, Requirement, Fact, Person, Product.
- **Fact:** A relationship (edge) connecting entities, e.g., "X relates to Y".

---

## 2. Agent Workflow

### A. Before Acting

- **Search for relevant knowledge:**
  - Use `search_nodes` to find entities (Preferences, Procedures, Requirements, etc.).
  - Use `search_facts` to retrieve relationships relevant to your task.
  - Filter by entity type or group if possible.
  - Review all matches before proceeding.

### B. Storing New/Updated Information

- **Capture immediately:**
  - Use `add_episode` to store new Requirements, Preferences, Procedures, or Facts.
  - For structured info, use `source="json"` to extract entities/relations.
  - Split complex info into shorter, clear entries.
- **Flag updates:**  
  - When modifying, clearly indicate the change and only add what's new.
- **Categorize:**  
  - Label episodes/entities clearly for easy retrieval.
  - Use group IDs when needed to scope data.

### C. During Tasks

- **Respect and apply memory:**
  - Align actions/outputs with Preferences and Requirements found.
  - Follow Procedures exactly if relevant.
  - Integrate relevant Facts into outputs and reasoning.
  - Stay consistent with previously stored knowledge.

### D. Best Practices

- **Search before adding/recommending:**  
  - Always check for existing info before creating or suggesting new entries.
- **Comprehensive search:**  
  - For multi-entity tasks, use both node and fact searches; use node UUID to focus context.
- **Prioritize specificity:**  
  - Prefer specific over general entries if both exist.
- **Proactively encode patterns:**  
  - Capture repeated user behaviors/preferences as new nodes or procedures.

### E. Handling Ambiguity

- If entity/relationship is missing, request clarification or note the gap.
- If data is conflicting/inconsistent, flag for user confirmation before updating.

---

## 3. Example Tool Usage

- **Add a Requirement:**  
  `add_episode(name="Export Preference", episode_body="User prefers CSV export.", source="text")`
- **Add Structured Data:**  
  `add_episode(name="User Profile", episode_body='{"name": "Alice", "role": "Analyst"}', source="json")`
- **Search for Facts:**  
  `search_facts(query="file export format", entity_type="Preference")`

---

## 4. Reference: Graphiti Tools

- `add_episode`: Store episode (text, JSON, message)
- `search_nodes`: Find node summaries (entities)
- `search_facts`: Retrieve relationships (edges)
- `delete_entity_edge`: Remove edge
- `delete_episode`: Remove episode
- `get_entity_edge`: Get edge by UUID
- `get_episodes`: Get recent episodes by group
- `clear_graph`: Reset graph
- `get_status`: Check server status

---

**Principle:**  
_The knowledge graph is the agent’s authoritative memory. Always use it to align with user preferences, requirements, and factual context._
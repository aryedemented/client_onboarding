from collections import defaultdict, deque
from typing import Dict, Union, List


from collections import defaultdict, deque

from matplotlib import pyplot as plt


# TODO: handle it later
def to_numeric(s):
    try:
        return float(s)
    except ValueError:
        return 1


def build_schedule(recipe_dict):
    # Step 1: Build graph from edges
    graph = defaultdict(list)
    indegree = defaultdict(int)
    nodes = set()
    if "edges" not in recipe_dict or "resources" not in recipe_dict:
        return []

    for edge in recipe_dict["edges"]:
        src = edge["from"]
        tgt = edge["to"]
        graph[src].append(tgt)
        indegree[tgt] += 1
        nodes.update([src, tgt])

    # Step 2: Topological sort
    queue = deque([node for node in nodes if indegree[node] == 0])
    topo_order = []
    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    # Step 3: Build resource time lookup
    prep_time = {
        res["name"]: to_numeric(res.get("preparation_time", 0)) or 0
        for res in recipe_dict.get("resources", [])
    }

    # Step 4: Assign start and end times
    start_time = {}
    end_time = {}
    for node in topo_order:
        parents = [src for src, tgts in graph.items() if node in tgts]
        max_parent_end = max((end_time.get(p, 0) for p in parents), default=0)
        duration = prep_time.get(node, 0)
        start_time[node] = max_parent_end
        end_time[node] = max_parent_end + to_numeric(duration)

    # Step 5: Extract only real resources with duration
    schedule = [
        {
            "resource": node,
            "start": start_time[node],
            "end": end_time[node]
        }
        for node in topo_order if prep_time.get(node, 0) > 0
    ]
    return schedule


def plot_schedule(scheduler_dict: List[Dict]):
    fig, ax = plt.subplots(figsize=(8, 3))
    print(scheduler_dict)
    resource_indices = {res: idx for idx, res in enumerate(set([s["resource"] for s in scheduler_dict]))}
    colors = plt.cm.tab10.colors
    unique_resources = list(set(entry["resource"] for entry in scheduler_dict))
    for idx, entry in enumerate(scheduler_dict):
        y_pos = resource_indices[entry["resource"]]
        ax.broken_barh([(entry["start"], entry["end"] - entry["start"])], (y_pos - 0.4, 0.8),
                       facecolors=colors[idx % len(colors)])
        ax.text(entry["start"] + 0.1, y_pos, entry["resource"], va='center', ha='left', fontsize=8, color='white')

    ax.set_yticks(list(resource_indices.values()))
    ax.set_yticklabels(list(resource_indices.keys()))
    ax.set_xlabel("Time (units)")
    ax.set_title("Resource Occupancy Gantt Chart")
    ax.grid(True)
    fig.show()
    # st.pyplot(fig)


if __name__ == '__main__':
    sample_recipe = {
        "edges": [
            {"from": "בצק", "to": "תבנית"},
            {"from": "רוטב עגבניות", "to": "תבנית"},
            {"from": "תבנית", "to": "תנור"}
        ],
        "resources": [
            {"name": "תנור", "preparation_time": "15 sec"},
            {"name": "תבנית", "preparation_time": 3}
        ]
    }
    schedule = build_schedule(sample_recipe)
    plot_schedule(schedule)
    print(schedule)

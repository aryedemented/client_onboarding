import os
from typing import Dict, List


from collections import defaultdict, deque

from matplotlib import pyplot as plt, cm
import sys

# Add the repo root (parent of client_boarding) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scan_text_recipes.utils.paths import PROJECT_ROOT
from scan_text_recipes.uploader_tool.src.st_utils import reshape_hebrew
from scan_text_recipes.utils.utils import read_yaml


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
        res["id"]: to_numeric(res.get("usage_time", 0)) or 0
        for res in recipe_dict.get("resources", [])
    }
    resource_names = {resource['id']: resource['name'] for resource in recipe_dict.get("resources", [])}
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
            "resource": resource_names[node],
            "start": start_time[node],
            "end": end_time[node]
        }
        for node in topo_order if prep_time.get(node, 0) > 0
    ]
    return schedule


def plot_schedule(scheduler_dict: List[Dict],dpi: int = 800):
    fig, ax = plt.subplots(figsize=(6, 0.8), dpi=dpi)
    cmap = cm.get_cmap('Pastel1')

    # Assign a unique color to each resource using the colormap
    unique_resources = list({s["resource"] for s in scheduler_dict})
    resource_indices = {res: idx for idx, res in enumerate(unique_resources)}
    resource_color_map = {
        res: cmap(i / max(len(unique_resources) - 1, 1))  # avoid division by zero
        for i, res in enumerate(unique_resources)
    }

    # Plot each resource's occupancy strip
    for entry in scheduler_dict:
        y_pos = resource_indices[entry["resource"]]
        color = resource_color_map[entry["resource"]]
        ax.broken_barh(
            [(entry["start"], entry["end"] - entry["start"])],
            (y_pos - 0.4, 0.8),
            facecolors=color
        )
        ax.text(
            entry["start"] + 0.1,
            y_pos,
            reshape_hebrew(entry["resource"]),
            va='center',
            ha='left',
            fontsize=5,
            color='black'
        )

    # Clean aesthetics
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis='x', labelsize=5)
    ax.set_yticklabels([])
    ax.tick_params(axis='y', which='both', left=False, labelleft=False)
    ax.set_xlabel("Time (min)", fontsize=3)
    ax.set_title("Resource Occupancy Gantt Chart", fontsize=5)
    ax.grid(False)
    return fig


if __name__ == '__main__':
    sample_recipe = {
        "edges": [
            {"from": "בצק", "to": "תבנית"},
            {"from": "רוטב עגבניות", "to": "תבנית"},
            {"from": "תבנית", "to": "תנור"}
        ],
        "resources": [
            {"name": "תנור", "usage_time": "15 sec"},
            {"name": "תבנית", "usage_time": 3}
        ]
    }
    sample_recipe = read_yaml(os.path.join(PROJECT_ROOT, "..", "structured_recipes", f"{'bruschetta'}.yaml"))
    schedule = build_schedule(sample_recipe)
    plot_schedule(schedule, dpi=200)
    print(schedule)
    plt.show()
    ...
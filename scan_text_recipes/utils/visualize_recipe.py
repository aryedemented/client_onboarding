import os

import graphviz

from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.utils.utils import read_yaml


def create_recipe_graph(data):
    dot = graphviz.Digraph(format="svg")  # Use SVG for tooltips
    dot.attr(rankdir="LR")

    # Add ingredient nodes with tooltips
    for ingredient in data.get("ingredients", []):
        tooltip_text = ingredient["instructions"]
        dot.node(str(ingredient["id"]), label=f"{ingredient['name']}\n{ingredient['quantity']}", shape="ellipse", tooltip=tooltip_text, style="filled", fillcolor="lightgreen")

    # Add resource nodes with tooltips
    for resource in data.get("resources", []):
        tooltip_text = resource["instructions"]
        dot.node(str(resource["id"]), label=f"{resource['name']}\n{resource['usage_time']}", shape="box", tooltip=tooltip_text, style="filled", illcolor="lightblue")

    # Add edges with instructions as labels
    for edge in data.get("edges", []):
        dot.edge(str(edge["from"]), str(edge["to"]), label=edge["instructions"])

    return dot


if __name__ == '__main__':
    recipe_filename = "pizza_simplified"
    recipe_data = read_yaml(os.path.join(PROJECT_ROOT, "..", "structured_recipes", f"{recipe_filename}.yaml"))
    graph = create_recipe_graph(recipe_data)
    graph.render(os.path.join(PROJECT_ROOT, "..", "structured_recipes", f"{recipe_filename}"), view=True)  # Saves and opens the graph
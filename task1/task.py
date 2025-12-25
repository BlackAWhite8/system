import math
from collections import defaultdict, deque
from typing import Tuple


def task(s: str, root_id: str) -> Tuple[float, float]:

    edges = []
    nodes = set()

    for line in s.strip().split('\n'):
        if line.strip():
            parts = line.split(',')
            if len(parts) >= 2:
                child, parent = parts[0].strip(), parts[1].strip()
                edges.append((child, parent))
                nodes.add(child)
                nodes.add(parent)

    graph = defaultdict(list)
    for child, parent in edges:
        graph[parent].append(child)

    def analyze_tree(root):
        level_stats = defaultdict(int)
        children_stats = defaultdict(int)

        queue = deque([(root, 0)])

        while queue:
            node, level = queue.popleft()
            level_stats[level] += 1

            children = graph.get(node, [])
            children_count = len(children)
            children_stats[children_count] += 1

            for child in children:
                queue.append((child, level + 1))

        return level_stats, children_stats

    level_stats, children_stats = analyze_tree(root_id)

    total_nodes = len(nodes)
    entropy_level = 0.0

    for level, count in level_stats.items():
        p = count / total_nodes
        if p > 0:
            entropy_level -= p * math.log2(p)

    entropy_children = 0.0

    for children_count, count in children_stats.items():
        p = count / total_nodes
        if p > 0:
            entropy_children -= p * math.log2(p)

    entropy = (entropy_level + entropy_children) / 2

    max_possible_entropy = math.log2(total_nodes) if total_nodes > 0 else 0

    if max_possible_entropy > 0:
        structural_complexity = entropy / max_possible_entropy
    else:
        structural_complexity = 0.0

    entropy = round(entropy, 1)
    structural_complexity = round(structural_complexity, 1)

    return entropy, structural_complexity


if __name__ == "__main__":
    csv_data = """A,root
B,A
C,A
D,B
E,B
F,C
G,C"""

    root = "root"
    result = task(csv_data, root)
    print(f"Энтропия: {result[0]}, Структурная сложность: {result[1]}")
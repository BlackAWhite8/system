import csv
from io import StringIO


def main(csv_string):
    reader = csv.reader(StringIO(csv_string))
    edges = list(reader)
    if not edges:
        return []

    vertices = set()
    for edge in edges:
        if len(edge) >= 2:
            vertices.add(int(edge[0]))
            vertices.add(int(edge[1]))

    if not vertices:
        return []

    sorted_vertices = sorted(vertices)
    n = len(sorted_vertices)
    vertex_to_index = {vertex: idx for idx, vertex in enumerate(sorted_vertices)}
    matrix = [[0] * n for _ in range(n)]

    for edge in edges:
        if len(edge) >= 2:
            from_vertex = int(edge[0])
            to_vertex = int(edge[1])
            i = vertex_to_index[from_vertex]
            j = vertex_to_index[to_vertex]
            matrix[i][j] = 1
    return matrix


if __name__ == "__main__":
    example_csv = """0,1
0,2
1,2
1,3
2,3"""

    result = main(example_csv)
    print("Матрица смежности:")
    for row in result:
        print(row)
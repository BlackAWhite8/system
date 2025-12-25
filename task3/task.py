import json
from typing import List, Dict, Any, Set
from collections import defaultdict


def process_rankings(json_str1: str, json_str2: str, variant: int = 1) -> str:


    def parse_ranking(json_str: str) -> List[List[str]]:

        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
            else:
                raise ValueError("Некорректный формат ранжировки")
        except json.JSONDecodeError:
            raise ValueError("Некорректный JSON")

    ranking1 = parse_ranking(json_str1)
    ranking2 = parse_ranking(json_str2)

    if variant == 1:
        return json.dumps(find_contradiction_core(ranking1, ranking2))
    else:
        return json.dumps(find_consistent_ranking(ranking1, ranking2))


def find_contradiction_core(ranking1: List[List[str]], ranking2: List[List[str]]) -> List[List[str]]:

    all_elements = set()
    for cluster in ranking1 + ranking2:
        all_elements.update(cluster)

    # Создаем словари позиций для каждой ранжировки
    pos1 = get_element_positions(ranking1)
    pos2 = get_element_positions(ranking2)

    # Находим противоречивые пары
    contradictions = []

    elements_list = list(all_elements)
    for i in range(len(elements_list)):
        for j in range(i + 1, len(elements_list)):
            elem1, elem2 = elements_list[i], elements_list[j]

            # Проверяем порядок в обеих ранжировках
            order1 = compare_positions(pos1[elem1], pos1[elem2])
            order2 = compare_positions(pos2[elem1], pos2[elem2])

            # Если порядок разный - это противоречие
            if order1 != order2 and order1 is not None and order2 is not None:
                contradictions.append([elem1, elem2])

    return contradictions


def find_consistent_ranking(ranking1: List[List[str]], ranking2: List[List[str]]) -> List[List[str]]:

    all_elements = set()
    for cluster in ranking1 + ranking2:
        all_elements.update(cluster)

    dominance_matrix = create_dominance_matrix(ranking1, ranking2, all_elements)

    return build_consistent_ranking(dominance_matrix, all_elements)


def get_element_positions(ranking: List[List[str]]) -> Dict[str, tuple]:

    positions = {}
    for level, cluster in enumerate(ranking):
        for pos_in_cluster, element in enumerate(cluster):
            positions[element] = (level, pos_in_cluster)
    return positions


def compare_positions(pos1: tuple, pos2: tuple) -> int:

    level1, pos_in_cluster1 = pos1
    level2, pos_in_cluster2 = pos2

    if level1 < level2:
        return 1
    elif level1 > level2:
        return -1
    else:
        if pos_in_cluster1 < pos_in_cluster2:
            return 1
        elif pos_in_cluster1 > pos_in_cluster2:
            return -1
        else:
            return 0


def create_dominance_matrix(ranking1: List[List[str]], ranking2: List[List[str]],
                            elements: Set[str]) -> Dict[str, Dict[str, int]]:

    pos1 = get_element_positions(ranking1)
    pos2 = get_element_positions(ranking2)

    matrix = {elem: {} for elem in elements}
    elements_list = list(elements)

    for i in range(len(elements_list)):
        for j in range(i + 1, len(elements_list)):
            elem1, elem2 = elements_list[i], elements_list[j]

            rel1 = compare_positions(pos1[elem1], pos1[elem2])
            rel2 = compare_positions(pos2[elem1], pos2[elem2])

            if rel1 == rel2 and rel1 != 0:
                value = rel1
            else:
                value = 0

            matrix[elem1][elem2] = value
            matrix[elem2][elem1] = -value

    return matrix


def build_consistent_ranking(matrix: Dict[str, Dict[str, int]],
                             elements: Set[str]) -> List[List[str]]:

    element_strength = {}
    for elem in elements:
        strength = 0
        for other_elem in elements:
            if elem != other_elem and matrix[elem].get(other_elem, 0) == 1:
                strength += 1
        element_strength[elem] = strength

    sorted_elements = sorted(elements, key=lambda x: element_strength[x], reverse=True)

    ranking = []
    current_cluster = []
    current_strength = None

    for elem in sorted_elements:
        if element_strength[elem] != current_strength:
            if current_cluster:
                ranking.append(current_cluster)
            current_cluster = [elem]
            current_strength = element_strength[elem]
        else:
            current_cluster.append(elem)

    if current_cluster:
        ranking.append(current_cluster)

    return ranking



if __name__ == "__main__":
    ranking1_json = json.dumps([["A", "B"], ["C"], ["D", "E"]])
    ranking2_json = json.dumps([["A"], ["B", "C"], ["D", "E"]])

    result1 = process_rankings(ranking1_json, ranking2_json, variant=1)
    print("Ядро противоречий:", result1)

    # Вариант 2: Согласованная кластерная ранжировка
    result2 = process_rankings(ranking1_json, ranking2_json, variant=2)
    print("Согласованная ранжировка:", result2)
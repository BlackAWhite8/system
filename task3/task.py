import json
from typing import List, Dict, Set, Tuple
from collections import defaultdict, deque


class ClusterRanking:

    def __init__(self, ranking_data: dict):

        self.ranking = ranking_data.get("ranking", [])
        self.elements = self._extract_elements()
        self.cluster_map = self._build_cluster_map()

    def _extract_elements(self) -> Set[str]:
        """Извлечение всех уникальных элементов из ранжировки"""
        elements = set()
        for cluster in self.ranking:
            elements.update(cluster)
        return elements

    def _build_cluster_map(self) -> Dict[str, int]:
        """Построение отображения элемента на номер кластера"""
        cluster_map = {}
        for idx, cluster in enumerate(self.ranking):
            for element in cluster:
                cluster_map[element] = idx
        return cluster_map

    def get_cluster(self, element: str) -> int:
        """Получение номера кластера для элемента"""
        return self.cluster_map.get(element, -1)

    def get_relation(self, a: str, b: str) -> str:

        if a not in self.cluster_map or b not in self.cluster_map:
            return "?"

        cluster_a = self.cluster_map[a]
        cluster_b = self.cluster_map[b]

        if cluster_a == cluster_b:
            return "="
        elif cluster_a < cluster_b:
            return "<"
        else:
            return ">"


def find_contradictions(ranking1: ClusterRanking, ranking2: ClusterRanking) -> List[Tuple[str, str]]:
    """
    Нахождение ядра противоречий между двумя ранжировками

    Ядро противоречий - это пары элементов, для которых отношения
    в двух ранжировках противоречат друг другу
    """
    contradictions = []
    elements = sorted(ranking1.elements.union(ranking2.elements))

    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            a, b = elements[i], elements[j]

            rel1 = ranking1.get_relation(a, b)
            rel2 = ranking2.get_relation(a, b)

            # Пропускаем если один из элементов отсутствует в какой-либо ранжировке
            if rel1 == "?" or rel2 == "?":
                continue

            # Проверяем противоречия
            if (rel1 == "<" and rel2 == ">") or (rel1 == ">" and rel2 == "<"):
                contradictions.append((a, b))

    return contradictions


def find_transitive_closure(relations: Dict[Tuple[str, str], str]) -> Dict[Tuple[str, str], str]:

    elements = set()
    for (a, b) in relations.keys():
        elements.add(a)
        elements.add(b)

    elements = list(elements)
    closure = relations.copy()

    # Используем алгоритм Флойда-Уоршелла для нахождения транзитивного замыкания
    for k in elements:
        for i in elements:
            for j in elements:
                if i == j:
                    continue

                # Если i < k и k < j, то i < j
                if (i, k) in closure and closure[(i, k)] == "<" and \
                        (k, j) in closure and closure[(k, j)] == "<":
                    closure[(i, j)] = "<"

                # Если i > k и k > j, то i > j
                elif (i, k) in closure and closure[(i, k)] == ">" and \
                        (k, j) in closure and closure[(k, j)] == ">":
                    closure[(i, j)] = ">"

    return closure


def build_consistent_ranking(ranking1: ClusterRanking, ranking2: ClusterRanking) -> List[List[str]]:

    # Собираем все элементы
    all_elements = sorted(ranking1.elements.union(ranking2.elements))

    graph = defaultdict(set)
    indegree = defaultdict(int)

    for element in all_elements:
        indegree[element] = 0

    # Собираем отношения из обеих ранжировок
    relations = {}

    for i in range(len(all_elements)):
        for j in range(len(all_elements)):
            if i == j:
                continue

            a, b = all_elements[i], all_elements[j]

            # Получаем отношения из обеих ранжировок
            rel1 = ranking1.get_relation(a, b)
            rel2 = ranking2.get_relation(a, b)

            if rel1 == rel2 and rel1 in ["<", ">"]:
                relations[(a, b)] = rel1
                if rel1 == "<":
                    graph[a].add(b)
                else:
                    graph[b].add(a)
            elif (rel1 == "=" and rel2 in ["<", ">"]) or (rel2 == "=" and rel1 in ["<", ">"]):
                rel = rel1 if rel1 != "=" else rel2
                relations[(a, b)] = rel
                if rel == "<":
                    graph[a].add(b)
                else:
                    graph[b].add(a)

            elif (rel1 == "<" and rel2 == ">") or (rel1 == ">" and rel2 == "<"):
                relations[(a, b)] = rel1
                if rel1 == "<":
                    graph[a].add(b)
                else:
                    graph[b].add(a)

    relations = find_transitive_closure(relations)

    graph = defaultdict(set)
    for (a, b), rel in relations.items():
        if rel == "<":
            graph[a].add(b)

    indegree = defaultdict(int)
    for element in all_elements:
        indegree[element] = 0

    for u in graph:
        for v in graph[u]:
            indegree[v] += 1

    #сортировка
    result_clusters = []
    visited = set()

    while len(visited) < len(all_elements):
        zero_indegree = [elem for elem in all_elements
                         if indegree[elem] == 0 and elem not in visited]

        if not zero_indegree:

            for elem in all_elements:
                if elem not in visited:
                    zero_indegree = [elem]
                    break

        current_cluster = []

        for elem in zero_indegree:
            if elem not in visited:
                current_cluster.append(elem)
                visited.add(elem)

                # Уменьшаем степень соседей
                for neighbor in graph[elem]:
                    indegree[neighbor] -= 1

        # Группируем элементы в одном кластере, если они были в одном кластере в исходных ранжировках
        clustered_current = []
        temp_cluster = []

        for elem in current_cluster:
            if temp_cluster:
                last_elem = temp_cluster[-1]
                if (ranking1.get_relation(last_elem, elem) == "=" and
                        ranking2.get_relation(last_elem, elem) == "="):
                    temp_cluster.append(elem)
                else:
                    clustered_current.append(temp_cluster.copy())
                    temp_cluster = [elem]
            else:
                temp_cluster = [elem]

        if temp_cluster:
            clustered_current.append(temp_cluster)

        result_clusters.extend(clustered_current)

    return result_clusters


def main(json_str1: str, json_str2: str) -> str:
    """
    Основная функция для согласования экспертных оценок

    Args:
        json_str1: JSON-строка с первой ранжировкой
        json_str2: JSON-строка со второй ранжировкой

    Returns:
        JSON-строка с согласованной кластерной ранжировкой

    """
    try:
        # Парсим входные данные
        data1 = json.loads(json_str1)
        data2 = json.loads(json_str2)

        # Создаем объекты ранжировок
        ranking1 = ClusterRanking(data1)
        ranking2 = ClusterRanking(data2)

        # Этап 1: Находим ядро противоречий
        contradictions = find_contradictions(ranking1, ranking2)

        # Этап 2: Строим согласованную ранжировку
        consistent_ranking = build_consistent_ranking(ranking1, ranking2)

        # Формируем результат
        result = {
            "contradictions_core": contradictions,
            "consistent_ranking": consistent_ranking
        }

        return json.dumps(result, ensure_ascii=False)

    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Ошибка парсинга JSON: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Ошибка обработки: {str(e)}"})


# Пример использования
if __name__ == "__main__":
    # Пример входных данных
    ranking1_example = '{"ranking": [["a", "b"], ["c"], ["d", "e"]]}'
    ranking2_example = '{"ranking": [["a"], ["b", "c"], ["d"], ["e"]]}'

    result = main(ranking1_example, ranking2_example)
    print("Результат согласования:")
    print(result)

    # Другой пример
    ranking3_example = '{"ranking": [["x", "y"], ["z"]]}'
    ranking4_example = '{"ranking": [["y"], ["x", "z"]]}'

    result2 = main(ranking3_example, ranking4_example)
    print("\nВторой пример:")
    print(result2)
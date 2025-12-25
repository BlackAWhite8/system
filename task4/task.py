import json
import math
from typing import Dict, List, Tuple, Optional
from enum import Enum


class FuzzySetType(Enum):
    """Типы функций принадлежности"""
    TRIANGULAR = "triangular"
    TRAPEZOIDAL = "trapezoidal"
    GAUSSIAN = "gaussian"


class MembershipFunction:
    """Класс для работы с функциями принадлежности"""

    @staticmethod
    def triangular(x: float, params: List[float]) -> float:
        """
        Треугольная функция принадлежности

        """
        a, b, c = params
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        else:  # b < x < c
            return (c - x) / (c - b)

    @staticmethod
    def trapezoidal(x: float, params: List[float]) -> float:
        """
        Трапециевидная функция принадлежности

        """
        a, b, c, d = params
        if x <= a or x >= d:
            return 0.0
        elif a < x < b:
            return (x - a) / (b - a)
        elif b <= x <= c:
            return 1.0
        else:  # c < x < d
            return (d - x) / (d - c)

    @staticmethod
    def gaussian(x: float, params: List[float]) -> float:
        """
        Гауссовская функция принадлежности

        """
        mean, sigma = params
        return math.exp(-((x - mean) ** 2) / (2 * sigma ** 2))

    @staticmethod
    def evaluate(x: float, func_type: str, params: List[float]) -> float:
        """
        Вычисление значения функции принадлежности

        """
        func_type = func_type.lower()

        if func_type == FuzzySetType.TRIANGULAR.value:
            return MembershipFunction.triangular(x, params)
        elif func_type == FuzzySetType.TRAPEZOIDAL.value:
            return MembershipFunction.trapezoidal(x, params)
        elif func_type == FuzzySetType.GAUSSIAN.value:
            return MembershipFunction.gaussian(x, params)
        else:
            raise ValueError(f"Неизвестный тип функции: {func_type}")


class LinguisticVariable:
    """Класс для работы с лингвистической переменной"""

    def __init__(self, name: str, terms: Dict[str, Dict]):
        """
        Инициализация лингвистической переменной

        """
        self.name = name
        self.terms = terms
        self.term_values = {}  # Для хранения текущих значений принадлежности

    def fuzzify(self, x: float) -> Dict[str, float]:
        """
        Фаззификация - вычисление степеней принадлежности для всех термов

        """
        result = {}
        for term, config in self.terms.items():
            func_type = config.get("type", "triangular")
            params = config.get("params", [])
            result[term] = MembershipFunction.evaluate(x, func_type, params)

        self.term_values = result
        return result

    def get_membership(self, term: str, x: float) -> float:
        """
        Получение степени принадлежности для конкретного терма

        """
        if term not in self.terms:
            return 0.0

        config = self.terms[term]
        func_type = config.get("type", "triangular")
        params = config.get("params", [])

        return MembershipFunction.evaluate(x, func_type, params)


class FuzzyRule:
    """Класс для работы с нечеткими правилами"""

    def __init__(self, rule_data: Dict):

        self.condition = rule_data.get("if", {})
        self.conclusion = rule_data.get("then", {})

    def evaluate(self, input_values: Dict[str, Dict[str, float]]) -> float:
        """
        Вычисление степени активации правила

        """
        activation = 1.0

        for variable, term in self.condition.items():
            if variable in input_values and term in input_values[variable]:
                # Используем минимальную активацию (логическое И)
                activation = min(activation, input_values[variable][term])
            else:
                return 0.0

        return activation

    def get_conclusion_variable(self) -> str:
        """Получение имени выходной переменной"""
        return list(self.conclusion.keys())[0] if self.conclusion else ""

    def get_conclusion_term(self) -> str:
        """Получение имени выходного терма"""
        variable = self.get_conclusion_variable()
        return self.conclusion.get(variable, "") if variable else ""


class FuzzyInference:
    """Класс для выполнения нечеткого логического вывода"""

    def __init__(self, rules: List[FuzzyRule]):
        self.rules = rules

    def infer(self, input_values: Dict[str, float],
              output_var: LinguisticVariable) -> Dict[str, float]:
        rule_activations = {}
        for i, rule in enumerate(self.rules):
            activation = rule.evaluate(input_values)
            if activation > 0:
                rule_activations[i] = {
                    'activation': activation,
                    'conclusion_var': rule.get_conclusion_variable(),
                    'conclusion_term': rule.get_conclusion_term()
                }

        # метод MAX
        aggregated_output = {}
        for term in output_var.terms.keys():
            max_activation = 0.0
            for rule_data in rule_activations.values():
                if rule_data['conclusion_term'] == term:
                    max_activation = max(max_activation, rule_data['activation'])
            if max_activation > 0:
                aggregated_output[term] = max_activation

        return aggregated_output


class FuzzyController:

    def __init__(self, temperature_var: LinguisticVariable,
                 heating_var: LinguisticVariable,
                 rules: List[FuzzyRule]):

        self.temperature_var = temperature_var
        self.heating_var = heating_var
        self.rules = rules
        self.inference = FuzzyInference(rules)

    def control(self, temperature: float) -> float:

        temp_memberships = self.temperature_var.fuzzify(temperature)

        rule_inputs = {
            "temperature": temp_memberships
        }

        fuzzy_output = self.inference.infer(rule_inputs, self.heating_var)

        return self._defuzzify_cog(fuzzy_output)

    def _defuzzify_cog(self, fuzzy_set: Dict[str, float]) -> float:
        """
        Дефаззификация методом центра тяжести
        """
        if not fuzzy_set:
            return 0.0

        numerator = 0.0
        denominator = 0.0

        for term, activation in fuzzy_set.items():
            if activation <= 0:
                continue

            config = self.heating_var.terms[term]
            func_type = config.get("type", "triangular")
            params = config.get("params", [])

            if func_type == FuzzySetType.TRIANGULAR.value and len(params) == 3:
                center = params[1]
            elif func_type == FuzzySetType.TRAPEZOIDAL.value and len(params) == 4:
                center = (params[1] + params[2]) / 2
            elif func_type == FuzzySetType.GAUSSIAN.value and len(params) == 2:
                center = params[0]
            else:
                center = sum(params) / len(params) if params else 0

            if func_type == FuzzySetType.TRIANGULAR.value and len(params) == 3:
                width = params[2] - params[0]
            elif func_type == FuzzySetType.TRAPEZOIDAL.value and len(params) == 4:
                width = params[3] - params[0]
            else:
                width = 1.0  # По умолчанию

            area = activation * width

            numerator += center * area
            denominator += area

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _defuzzify_mom(self, fuzzy_set: Dict[str, float]) -> float:
        """
        Дефаззификация методом среднего максимума

        """
        if not fuzzy_set:
            return 0.0

        max_activation = max(fuzzy_set.values())

        if max_activation <= 0:
            return 0.0

        max_terms = [term for term, activation in fuzzy_set.items()
                     if abs(activation - max_activation) < 1e-6]

        centers = []
        for term in max_terms:
            config = self.heating_var.terms[term]
            params = config.get("params", [])
            func_type = config.get("type", "triangular")

            if func_type == FuzzySetType.TRIANGULAR.value and len(params) == 3:
                center = params[1]
            elif func_type == FuzzySetType.TRAPEZOIDAL.value and len(params) == 4:
                center = (params[1] + params[2]) / 2
            elif func_type == FuzzySetType.GAUSSIAN.value and len(params) == 2:
                center = params[0]
            else:
                center = sum(params) / len(params) if params else 0

            centers.append(center)

        return sum(centers) / len(centers) if centers else 0.0


def parse_linguistic_variable(json_str: str, name: str) -> LinguisticVariable:
    data = json.loads(json_str)
    return LinguisticVariable(name, data)


def parse_rules(json_str: str) -> List[FuzzyRule]:
    data = json.loads(json_str)
    rules = []

    # Обрабатываем как одно правило или список правил
    if isinstance(data, dict):
        rules.append(FuzzyRule(data))
    elif isinstance(data, list):
        for rule_data in data:
            rules.append(FuzzyRule(rule_data))

    return rules


def main(temperature_json: str, heating_json: str,
         rules_json: str, current_temp: float) -> float:
    try:
        # Парсинг
        temperature_var = parse_linguistic_variable(temperature_json, "temperature")
        heating_var = parse_linguistic_variable(heating_json, "heating_level")
        rules = parse_rules(rules_json)

        # Создание контроллера
        controller = FuzzyController(temperature_var, heating_var, rules)

        # Вычисление управления
        optimal_heating = controller.control(current_temp)

        return optimal_heating

    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        return 0.0
    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        return 0.0



if __name__ == "__main__":

    temperature_json = json.dumps({
        "cold": {
            "type": "triangular",
            "params": [0, 10, 20]
        },
        "warm": {
            "type": "triangular",
            "params": [15, 25, 35]
        },
        "hot": {
            "type": "triangular",
            "params": [30, 40, 50]
        }
    })

    heating_json = json.dumps({
        "low": {
            "type": "triangular",
            "params": [0, 20, 40]
        },
        "medium": {
            "type": "triangular",
            "params": [30, 50, 70]
        },
        "high": {
            "type": "triangular",
            "params": [60, 80, 100]
        }
    })

    rules_json = json.dumps([
        {
            "if": {"temperature": "cold"},
            "then": {"heating_level": "high"}
        },
        {
            "if": {"temperature": "warm"},
            "then": {"heating_level": "medium"}
        },
        {
            "if": {"temperature": "hot"},
            "then": {"heating_level": "low"}
        }
    ])

    test_temperatures = [5, 15, 25, 35, 45]


    for temp in test_temperatures:
        heating = main(temperature_json, heating_json, rules_json, temp)
        print(f"Температура: {temp:2}°C -> Уровень нагрева: {heating:6.2f}")


import xml.etree.ElementTree as ET
import sys
import re

class ConfigLangProcessor:
    def __init__(self):
        # Инициализация словаря для хранения констант, определенных в XML
        self.constants = {}

    def parse_xml(self, xml_path):
        # Парсит XML-файл и возвращает его корневой элемент
        try:
            tree = ET.parse(xml_path)
            return tree.getroot()
        except ET.ParseError as e:
            # Вывод ошибки и завершение программы в случае неверного XML
            print(f"XML parsing error: {e}")
            sys.exit(1)

    def convert_to_ucl(self, element, level=0):
        """Преобразует XML-элемент в строку на языке UCL."""
        output = ""
        indent = "  " * level  # Отступ для вложенных уровней
        if element.tag == "dictionary":
            # Начало блока словаря
            output += indent + "@{\n"
            for child in element:
                # Обработка каждого элемента entry внутри dictionary
                if child.tag == "entry" and "name" in child.attrib:
                    name = child.attrib["name"]
                    if child.find("dictionary") is not None:
                        # Рекурсивная обработка вложенного словаря
                        output += f"{indent} {name} = " + self.convert_to_ucl(child.find("dictionary"), level + 1)
                    elif "value" in child.attrib:
                        # Обработка значения внутри entry
                        value = str(self.convert_value(child.attrib["value"]))  # Приведение к строке
                        output += f"{indent} {name} = {value};\n"
                    else:
                        # Ошибка, если entry не содержит ни value, ни вложенного dictionary
                        print(f"Error: Invalid dictionary entry in {element.tag}")
                        sys.exit(1)
            # Конец блока словаря
            output += indent + "}\n"
        elif element.tag == "define":
            # Обработка элемента define, добавление в словарь констант
            if "name" in element.attrib and "value" in element.attrib:
                name = element.attrib["name"]
                value = str(self.convert_value(element.attrib["value"]))  # Приведение к строке
                self.constants[name] = value
                output += f"{indent}(define {name} {value});\n"
            else:
                # Ошибка, если define не содержит name или value
                print(f"Error: Invalid define entry in {element.tag}")
                sys.exit(1)
        elif element.tag == "expression":
            # Обработка элемента expression, вычисление постфиксного выражения
            expr = element.attrib.get("value", "")
            result = self.eval_postfix(expr)
            output += f"{indent}?({expr}) // Result: {result}\n"
        else:
            # Ошибка при неизвестном теге XML
            print(f"Error: Unknown XML element {element.tag}")
            sys.exit(1)
        return output

    def convert_value(self, value):
        """Конвертирует строковое значение в UCL-формат."""
        if re.match(r"^-?\d+$", value):  # Проверка на целое число, включая отрицательные
            return int(value)
        elif value in self.constants:  # Если значение - имя константы
            const_value = self.constants[value]
            # Если значение константы - число, возвращаем его как int
            return int(const_value) if re.match(r"^-?\d+$", const_value) else const_value
        else:
            # Возвращаем строковое значение как есть (например, "localhost" или "cert.pem")
            return value

    def eval_postfix(self, expression):
        """Вычисляет выражение в постфиксной нотации."""
        stack = []
        tokens = expression.split()
        for token in tokens:
            # Если токен - целое число (включая отрицательные)
            if re.match(r"^-?\d+$", token):
                stack.append(int(token))
            # Если токен - имя константы, получаем значение
            elif token in self.constants:
                value = self.constants[token]
                # Если значение константы - целое число, преобразуем его в int
                stack.append(int(value) if re.match(r"^-?\d+$", str(value)) else value)
            elif token == "+":
                # Выполнение операции сложения
                b = stack.pop()
                a = stack.pop()
                # Проверка, что оба операнда - целые числа
                if isinstance(a, int) and isinstance(b, int):
                    stack.append(a + b)
                else:
                    print(f"Error: Non-integer values in addition operation: {a} + {b}")
                    sys.exit(1)
            elif token == "abs":
                # Выполнение операции абсолютного значения
                a = stack.pop()
                # Проверка, что значение является целым числом
                if isinstance(a, int):
                    stack.append(abs(a))
                else:
                    print(f"Error: Non-integer value in abs operation: {a}")
                    sys.exit(1)
            else:
                # Ошибка при неизвестном токене
                print(f"Error: Invalid token '{token}' in expression")
                sys.exit(1)
        return stack.pop()

    def process(self, xml_path):
        # Основной метод для обработки XML-файла
        root = self.parse_xml(xml_path)
        output = ""
        for element in root:
            # Преобразование каждого элемента XML в UCL-формат
            output += self.convert_to_ucl(element)
        return output


def main():
    # Проверка на наличие аргумента с путем к XML-файлу
    if len(sys.argv) != 2:
        print("Usage: python config_processor.py <path_to_xml_file>")
        sys.exit(1)

    xml_path = sys.argv[1]
    processor = ConfigLangProcessor()
    output = processor.process(xml_path)
    print(output)

# Запуск программы
if __name__ == "__main__":
    main()

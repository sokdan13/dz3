import xml.etree.ElementTree as ET
import sys
import re

class ConfigLangProcessor:
    def __init__(self):
        self.constants = {}

    def parse_xml(self, xml_path):
        try:
            tree = ET.parse(xml_path)
            return tree.getroot()
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            sys.exit(1)

    def convert_to_ucl(self, element, level=0):
        """Преобразует XML-элемент в строку на языке UCL."""
        output = ""
        indent = "  " * level  # отступ для вложенных уровней
        if element.tag == "dictionary":
            output += indent + "@{\n"
            for child in element:
                if child.tag == "entry" and "name" in child.attrib:
                    name = child.attrib["name"]
                    if child.find("dictionary") is not None:
                        # Рекурсивно обработаем вложенный словарь
                        output += f"{indent} {name} = " + self.convert_to_ucl(child.find("dictionary"), level + 1)
                    elif "value" in child.attrib:
                        value = str(self.convert_value(child.attrib["value"]))  # Приведение к строке
                        output += f"{indent} {name} = {value};\n"
                    else:
                        print(f"Error: Invalid dictionary entry in {element.tag}")
                        sys.exit(1)
            output += indent + "}\n"
        elif element.tag == "define":
            if "name" in element.attrib and "value" in element.attrib:
                name = element.attrib["name"]
                value = str(self.convert_value(element.attrib["value"]))  # Приведение к строке
                self.constants[name] = value
                output += f"{indent}(define {name} {value});\n"
            else:
                print(f"Error: Invalid define entry in {element.tag}")
                sys.exit(1)
        elif element.tag == "expression":
            expr = element.attrib.get("value", "")
            result = self.eval_postfix(expr)
            output += f"{indent}?({expr}) // Result: {result}\n"
        else:
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
                b = stack.pop()
                a = stack.pop()
                # Убедимся, что оба значения - целые числа перед сложением
                if isinstance(a, int) and isinstance(b, int):
                    stack.append(a + b)
                else:
                    print(f"Error: Non-integer values in addition operation: {a} + {b}")
                    sys.exit(1)
            elif token == "abs":
                a = stack.pop()
                # Проверяем, что значение - целое число для применения abs()
                if isinstance(a, int):
                    stack.append(abs(a))
                else:
                    print(f"Error: Non-integer value in abs operation: {a}")
                    sys.exit(1)
            else:
                print(f"Error: Invalid token '{token}' in expression")
                sys.exit(1)
        return stack.pop()

    def process(self, xml_path):
        root = self.parse_xml(xml_path)
        output = ""
        for element in root:
            output += self.convert_to_ucl(element)
        return output


def main():
    if len(sys.argv) != 2:
        print("Usage: python config_processor.py <path_to_xml_file>")
        sys.exit(1)

    xml_path = sys.argv[1]
    processor = ConfigLangProcessor()
    output = processor.process(xml_path)
    print(output)

if __name__ == "__main__":
    main()

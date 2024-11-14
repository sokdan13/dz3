import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET
from Project import ConfigLangProcessor  # Импорт из Project.py

class TestConfigLangProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = ConfigLangProcessor()

    # Тесты для функции parse_xml
    def test_parse_xml_valid(self):
        # Тестирует корректный XML-файл
        with patch("Project.ET.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ET.Element("root")
            root = self.processor.parse_xml("valid.xml")
            self.assertEqual(root.tag, "root")

    def test_parse_xml_invalid(self):
        # Тестирует ошибку парсинга XML
        with patch("Project.ET.parse", side_effect=ET.ParseError("Invalid XML")):
            with self.assertRaises(SystemExit):
                self.processor.parse_xml("invalid.xml")



    # Тесты для функции convert_to_ucl
    def test_convert_to_ucl_dictionary(self):
        # Тестирует корректное преобразование XML-элемента dictionary
        element = ET.Element("dictionary")
        entry = ET.SubElement(element, "entry", {"name": "key", "value": "42"})
        result = self.processor.convert_to_ucl(element)
        self.assertIn("@{\n key = 42;\n}\n", result)

    def test_convert_to_ucl_define(self):
        # Тестирует корректное преобразование XML-элемента define
        element = ET.Element("define", {"name": "PI", "value": "3.14"})
        result = self.processor.convert_to_ucl(element)
        self.assertIn("(define PI 3.14);\n", result)
        self.assertEqual(self.processor.constants["PI"], "3.14")

    def test_convert_to_ucl_expression(self):
        # Тестирует корректное преобразование XML-элемента expression
        element = ET.Element("expression", {"value": "3 4 +"})
        result = self.processor.convert_to_ucl(element)
        self.assertIn("?(3 4 +) // Result: 7\n", result)

    # Тесты для функции convert_value
    def test_convert_value_integer(self):
        # Тестирует конвертацию строки целого числа
        result = self.processor.convert_value("123")
        self.assertEqual(result, 123)

    def test_convert_value_constant(self):
        # Тестирует конвертацию имени константы
        self.processor.constants["HOST"] = "localhost"
        result = self.processor.convert_value("HOST")
        self.assertEqual(result, "localhost")

    def test_convert_value_string(self):
        # Тестирует конвертацию строки, которая не является числом или константой
        result = self.processor.convert_value("cert.pem")
        self.assertEqual(result, "cert.pem")

    # Тесты для функции eval_postfix
    def test_eval_postfix_addition(self):
        # Тестирует корректное выполнение сложения в постфиксной нотации
        self.processor.constants = {}
        result = self.processor.eval_postfix("3 4 +")
        self.assertEqual(result, 7)

    def test_eval_postfix_abs(self):
        # Тестирует корректное выполнение функции abs в постфиксной нотации
        result = self.processor.eval_postfix("-5 abs")
        self.assertEqual(result, 5)

    def test_eval_postfix_constant(self):
        # Тестирует использование констант в постфиксном выражении
        self.processor.constants["TEN"] = "10"
        result = self.processor.eval_postfix("TEN 2 +")
        self.assertEqual(result, 12)


if __name__ == "__main__":
    unittest.main()
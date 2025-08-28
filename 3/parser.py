import math
import re

# --- Вспомогательные функции для работы с восьмеричными числами ---

def octal_str_to_float(oct_str):
    """Преобразует восьмеричную строку (возможно, с дробной частью) в float."""
    if '.' in oct_str:
        integer_part_str, fractional_part_str = oct_str.split('.')
        integer_part = int(integer_part_str, 8)
        fractional_part = 0.0
        for i, digit in enumerate(fractional_part_str):
            fractional_part += int(digit, 8) * (8 ** -(i + 1))
        return float(integer_part) + fractional_part
    else:
        return float(int(oct_str, 8))

def format_value(value):
    """Форматирует числовое значение в восьмеричную строку для вывода."""
    if isinstance(value, complex):
        return f"{format_value(value.real)},{format_value(value.imag)}"
    if isinstance(value, float):
        if value < 0:
            return "-" + format_value(abs(value))
        integer_part = int(value)
        fractional_part = value - integer_part
        
        oct_integer = oct(integer_part)[2:]
        
        if fractional_part == 0:
            return oct_integer
            
        oct_fractional = []
        for _ in range(15):
            fractional_part *= 8
            digit = int(fractional_part)
            oct_fractional.append(str(digit))
            fractional_part -= digit
            if fractional_part == 0:
                break
        return f"{oct_integer}.{''.join(oct_fractional)}"
    if value < 0:
        return '-' + oct(abs(int(value)))[2:]
    return oct(int(value))[2:]


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.errors = []
        self.symbol_table = {}
        self.declared_variables = set()

    def report_error(self, message, start, end):
        self.errors.append((message, start, end))

    def consume(self, *expected_types):
        if self.current_token_index < len(self.tokens):
            current_token = self.tokens[self.current_token_index]
            if current_token.type in expected_types:
                self.current_token_index += 1
                return current_token
        return None

    def peek(self, offset=0):
        index = self.current_token_index + offset
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return None

    def parse(self):
        try:
            self.parse_Язык()
        except Exception:
            pass
        return self.symbol_table, self.errors

    def parse_Язык(self):
        start_token = self.peek()
        if not start_token or start_token.type != 'KEYWORD_START':
            start_pos = start_token.start if start_token else 0
            end_pos = start_token.end if start_token else 1
            msg = f'Язык должен начинаться словом "Start", найден "{start_token.value}"' if start_token else 'Язык должен начинаться словом "Start"'
            self.report_error(msg, start_pos, end_pos)
            raise Exception("Fatal Error")
        self.consume('KEYWORD_START')

        found_mnozh = False
        while self.peek() and self.peek().type == 'KEYWORD_ARRAY':
            found_mnozh = True
            self.parse_Множ()
        
        if not found_mnozh:
            next_token = self.peek()
            start = next_token.start if next_token else self.tokens[-1].end
            end = next_token.end if next_token else start + 1
            msg = f'Не обнаружен блок Множ. Блок Множ должен начинаться со слова "Array", найден "{next_token.value}"' if next_token else 'Не обнаружен блок Множ. Блок Множ должен начинаться со слова "Array"'
            self.report_error(msg, start, end)
            raise Exception("Fatal Error")

        next_token = self.peek()
        if next_token and next_token.type == 'IDENTIFIER':
            self.parse_Окончание()
        else:
            tok = self.peek() or self.tokens[-1]
            error_val = f'"{tok.value}"' if tok else "конец файла"
            self.report_error(f'ожидался блок Окончание (начинается с переменной), но найден {error_val}', tok.start, tok.end)
            raise Exception("Fatal Error")
        
        if self.peek() and self.peek().type == 'IDENTIFIER':
            tok = self.peek()
            self.report_error("блок Окончание может быть только один раз", tok.start, tok.end)
            raise Exception("Fatal Error")

        end_token = self.peek()
        if not end_token or end_token.type != 'KEYWORD_END':
            last_token = self.tokens[-1]
            start = end_token.start if end_token else last_token.end
            end = end_token.end if end_token else start + 1
            msg = f'Язык должен заканчиваться словом "End", найден "{end_token.value}"' if end_token else 'Язык должен заканчиваться словом "End"'
            self.report_error(msg, start, end)
            raise Exception("Fatal Error")
        
        self.consume('KEYWORD_END')

        if self.peek():
            tok = self.peek()
            self.report_error(f'После слова "End" присутствуют символы, найден "{tok.value}"', tok.start, tok.end)
            raise Exception("Fatal Error")


    def parse_Множ(self):
        array_token = self.consume('KEYWORD_ARRAY')
        if not self.peek() or self.peek().type not in ('NUMBER'):
            next_tok = self.peek() or array_token
            pos = next_tok.end if next_tok else len(self.tokens[-1].value)
            self.report_error('после "Array" должно следовать хотя бы одно число', pos, pos + 1)
            raise Exception("Empty Array block")

        while self.peek() and self.peek().type in ('NUMBER'):
            self.parse_число()

    def parse_число(self):
        start_tok = self.peek()
        if self.peek(1) and self.peek(1).type == 'PUNCTUATION_DOT':
            self.parse_вещ()
            if self.peek() and self.peek().type == 'PUNCTUATION_COMMA':
                self.consume('PUNCTUATION_COMMA')
                if self.peek() and self.peek().type == 'NUMBER' and self.peek(1) and self.peek(1).type == 'PUNCTUATION_DOT':
                     self.parse_вещ()
                else:
                    tok = self.peek() or self.tokens[-1]
                    self.report_error('Неверный формат комплексного числа, после "," ожидалось вещ', tok.start, tok.end)
                    raise Exception("Parsing Error: Incomplete complex number")
            return None
        elif start_tok.type == 'NUMBER':
            token = self.consume('NUMBER')
            try:
                int(token.value, 8)
            except ValueError:
                self.report_error(f'Неверный формат числа "{token.value}" (ожидались восьмеричные цифры от 0 до 7 включительно)', token.start, token.end)
                raise Exception("Invalid octal integer")
            return None
        else:
            self.report_error(f"Ожидалось число, но найдено '{start_tok.value}'", start_tok.start, start_tok.end)
            return None

    def parse_вещ(self):
        int_part = self.consume('NUMBER')
        if not int_part:
            tok = self.peek() or self.tokens[-1]
            self.report_error('Неверный формат вещественного числа, перед "." ожидалось цел', tok.start, tok.end)
            return 0.0

        dot = self.consume('PUNCTUATION_DOT')
        if not dot:
            self.report_error('Неверный формат вещественного числа, отсутствует "."', int_part.end, int_part.end + 1)
            return 0.0
            
        frac_part = self.consume('NUMBER')
        if not frac_part:
            self.report_error('Неверный формат вещественного числа, после "." ожидалось цел', dot.end, dot.end + 1)
            raise Exception("Parsing Error: Incomplete real number")
        
        try:
            return octal_str_to_float(f"{int_part.value}.{frac_part.value}")
        except ValueError:
            self.report_error(f'Неверный формат числа "{int_part.value}.{frac_part.value}" (ожидались восьмеричные цифры от 0 до 7 включительно)', int_part.start, frac_part.end)
            return 0.0
    
    def parse_Окончание(self):
        var_token = self.consume('IDENTIFIER')
        if not var_token:
            raise Exception("Fatal Error")
        
        if not re.fullmatch(r'[A-Za-z]{2}[0-7]{3}', var_token.value):
            self.report_error('переменная должна именоваться так: "буква буква цифра цифра цифра" (цифры от 0 до 7)', var_token.start, var_token.end)
            raise Exception("Invalid variable format")

        self.declared_variables.add(var_token.value)
        self.symbol_table[var_token.value] = 0

        equals_token = self.consume('PUNCTUATION_EQUALS')
        if not equals_token:
            self.report_error(f'Отсутствует "=" после переменной "{var_token.value}"', var_token.end, var_token.end + 1)
            raise Exception("Parsing Error")

        value = self.parse_Прав_часть(depth=0)
        self.symbol_table[var_token.value] = value

    def check_missing_operator(self, last_token):
        """FIX 3: Проверяет наличие оператора после значения."""
        next_tok = self.peek()
        if next_tok and next_tok.type in ('IDENTIFIER', 'NUMBER', 'PUNCTUATION_LBRACKET'):
            # Собрать полное значение для сообщения об ошибке (например, "4.1")
            full_value = last_token.value
            if hasattr(last_token, 'full_value'):
                full_value = last_token.full_value

            self.report_error(f'Отсутствует арифметический оператор', last_token.end, next_tok.start)
            raise Exception("Missing operator")

    def parse_Прав_часть(self, depth):
        result = self.parse_Блок1(depth)
        while self.peek() and self.peek().type in ('OPERATOR_PLUS', 'OPERATOR_MINUS'):
            op_token = self.consume('OPERATOR_PLUS', 'OPERATOR_MINUS')
            
            if not self.peek() or self.peek().type in ('OPERATOR_PLUS', 'OPERATOR_MINUS', 'OPERATOR_MULTIPLY', 'OPERATOR_DIVIDE', 'OPERATOR_POWER', 'KEYWORD_END', 'PUNCTUATION_RBRACKET'):
                next_tok = self.peek()
                if not next_tok or next_tok.type in ('KEYWORD_END', 'PUNCTUATION_RBRACKET'):
                     self.report_error(f'После арифметического оператора "{op_token.value}" нет вещественного числа.', op_token.start, op_token.end)
                else:
                    self.report_error(f'Не могут следовать два оператора подряд ("{op_token.value}" и "{next_tok.value}").', op_token.start, next_tok.end)
                raise Exception("Parsing Error")

            right = self.parse_Блок1(depth)
            if op_token.type == 'OPERATOR_PLUS':
                result += right
            else:
                result -= right
        return result

    def parse_Блок1(self, depth):
        result = self.parse_Блок2(depth)
        while self.peek() and self.peek().type in ('OPERATOR_MULTIPLY', 'OPERATOR_DIVIDE'):
            op_token = self.consume('OPERATOR_MULTIPLY', 'OPERATOR_DIVIDE')

            if not self.peek() or self.peek().type in ('OPERATOR_PLUS', 'OPERATOR_MINUS', 'OPERATOR_MULTIPLY', 'OPERATOR_DIVIDE', 'OPERATOR_POWER', 'KEYWORD_END', 'PUNCTUATION_RBRACKET'):
                next_tok = self.peek()
                if not next_tok or next_tok.type in ('KEYWORD_END', 'PUNCTUATION_RBRACKET'):
                     self.report_error(f'После арифметического оператора "{op_token.value}" нет вещественного числа.', op_token.start, op_token.end)
                else:
                    self.report_error(f'Не могут следовать два оператора подряд ("{op_token.value}" и "{next_tok.value}").', op_token.start, next_tok.end)
                raise Exception("Parsing Error")

            right = self.parse_Блок2(depth)
            if op_token.type == 'OPERATOR_MULTIPLY':
                result *= right
            else:
                if right == 0:
                    self.report_error('Ошибка: деление на ноль', op_token.start, self.tokens[self.current_token_index - 1].end)
                    raise Exception("Division by zero")
                result /= right
        return result

    def parse_Блок2(self, depth):
        result = self.parse_Блок3(depth)
        self.check_missing_operator(self.tokens[self.current_token_index - 1])

        while self.peek() and self.peek().type == 'OPERATOR_POWER':
            op_token = self.consume('OPERATOR_POWER')
            
            if not self.peek() or self.peek().type in ('OPERATOR_PLUS', 'OPERATOR_MINUS', 'OPERATOR_MULTIPLY', 'OPERATOR_DIVIDE', 'OPERATOR_POWER', 'KEYWORD_END', 'PUNCTUATION_RBRACKET'):
                next_tok = self.peek()
                if not next_tok or next_tok.type in ('KEYWORD_END', 'PUNCTUATION_RBRACKET'):
                     self.report_error(f'После арифметического оператора "{op_token.value}" нет вещественного числа.', op_token.start, op_token.end)
                else:
                    self.report_error(f'Не могут следовать два оператора подряд ("{op_token.value}" и "{next_tok.value}").', op_token.start, next_tok.end)
                raise Exception("Parsing Error")

            right = self.parse_Блок3(depth)
            self.check_missing_operator(self.tokens[self.current_token_index - 1])
            result **= right
        return result

    def parse_Блок3(self, depth):
        token = self.peek()

        # FIX 4: Проверка на лишнюю закрывающую скобку
        if token.type == 'PUNCTUATION_RBRACKET':
            self.report_error("Обнаружена закрывающая скобка ']' без соответствующей открывающей", token.start, token.end)
            raise Exception("Unmatched closing bracket")

        # FIX 5: Проверка на недопустимые типы скобок
        if token.type in ('INVALID_LPAREN', 'INVALID_RPAREN', 'INVALID_LBRACE', 'INVALID_RBRACE'):
             self.report_error(f"использование скобок '{token.value}' не допускается, используйте '[]'", token.start, token.end)
             raise Exception("Invalid bracket type")

        # FIX 2: Обработка унарного минуса/плюса
        sign = 1
        if token.type in ('OPERATOR_PLUS', 'OPERATOR_MINUS'):
            op_token = self.consume(token.type)
            if op_token.type == 'OPERATOR_MINUS':
                sign = -1
            token = self.peek() # Смотрим на следующий токен после знака

        if token.type == 'IDENTIFIER':
            var_token = self.consume('IDENTIFIER')
            if var_token.value not in self.declared_variables:
                 self.report_error(f"Ошибка: переменная '{var_token.value}' не объявлена", var_token.start, var_token.end)
                 return 0
            return self.symbol_table.get(var_token.value, 0) * sign

        if token.type == 'NUMBER' and self.peek(1) and self.peek(1).type == 'PUNCTUATION_DOT':
            # Сохраняем начальный токен для полного значения в сообщении об ошибке
            start_num_token = token
            value = self.parse_вещ()
            end_num_token = self.tokens[self.current_token_index - 1]
            # Создаем временный объект для передачи полного значения
            end_num_token.full_value = self.tokens[start_num_token.start:end_num_token.end+1]
            return value * sign
        
        # FIX 1: Ошибка для целых чисел в выражении
        if token.type == 'NUMBER':
            self.report_error('в выражении допускаются только вещественные числа (например, 7.0)', token.start, token.end)
            raise Exception("Integer in expression")

        if token.type == 'PUNCTUATION_LBRACKET':
            if depth >= 2:
                self.report_error("глубина вложенности скобок не может превышать 2", token.start, token.end)
                raise Exception("Nesting too deep")
            self.consume('PUNCTUATION_LBRACKET')
            result = self.parse_Прав_часть(depth + 1)
            
            if not self.peek() or self.peek().type != 'PUNCTUATION_RBRACKET':
                tok = self.peek() or self.tokens[self.current_token_index-1]
                self.report_error('отсутствует закрывающая скобка "]"', tok.start, tok.end)
                raise Exception("Missing closing bracket")

            self.consume('PUNCTUATION_RBRACKET')
            return result * sign

        if token.type == 'PUNCTUATION_DOT':
            self.report_error('Неверный формат вещественного числа, перед "." ожидалось цел', token.start, token.end)
            raise Exception("Parsing Error: Real number starting with a dot")
        
        self.report_error(f"неожиданный токен '{token.value}' в выражении", token.start, token.end)
        raise Exception("Parsing Error")
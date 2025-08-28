import re

# Use a list of tuples to define token patterns.
# The order is crucial: more specific patterns (like keywords) must come before more general ones.
TOKEN_SPECIFICATION = [
    # Keywords
    ('KEYWORD_START',   r'Start'),
    ('KEYWORD_END',     r'End'),
    ('KEYWORD_ARRAY',   r'Array'),

    # Operators (two-character operators first)
    ('OPERATOR_POWER',  r'\*\*'),
    ('OPERATOR_PLUS',   r'\+'),
    ('OPERATOR_MINUS',  r'-'),
    ('OPERATOR_MULTIPLY', r'\*'),
    ('OPERATOR_DIVIDE', r'\/'),

    # Punctuation
    ('PUNCTUATION_LBRACKET', r'\['),
    ('PUNCTUATION_RBRACKET', r'\]'),
    ('PUNCTUATION_EQUALS', r'='),
    ('PUNCTUATION_COMMA',  r','),
    ('PUNCTUATION_DOT',    r'\.'),

    # Invalid bracket types that the parser will catch
    ('INVALID_LPAREN', r'\('),
    ('INVALID_RPAREN', r'\)'),
    ('INVALID_LBRACE', r'\{'),
    ('INVALID_RBRACE', r'\}'),

    # Specific variable format. Must come before the general 'NAME' pattern.
    ('IDENTIFIER',      r'[A-Za-z]{2}[0-9]{3}'),
    
    # General pattern for any other word-like text (e.g., misspelled keywords).
    ('NAME',            r'[A-Za-z]+'),

    # Numbers (now accepts any digits; parser will validate octal)
    ('NUMBER',          r'[0-9]+'),

    # Ignored characters
    ('WHITESPACE',      r'\s+'),
    
    # Any other sequence of characters is an 'UNKNOWN' lexical error.
    ('UNKNOWN',         r'[^ \t\n\r\f\v+\-*/\[\]=,.\(\)\{\}]+') # Added invalid chars to exclusion
]

# Build the master regex from the specification list
TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION)

class Token:
    """Класс для представления токена."""
    def __init__(self, type, value, start, end):
        self.type = type
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return f"Token({self.type}, '{self.value}', pos {self.start}-{self.end})"


class Lexer:
    """Лексический анализатор, который разбивает текст на токены."""
    def __init__(self, text):
        self.text = text
        self.errors = []

    def tokenize(self):
        """
        Выполняет токенизацию входного текста.
        Возвращает список токенов и список ошибок.
        """
        tokens = []
        # Итерация по всем совпадениям в тексте
        for match in re.finditer(TOKEN_REGEX, self.text):
            token_type = match.lastgroup
            token_value = match.group(token_type)
            token_start = match.start()
            token_end = match.end()

            if token_type == 'WHITESPACE':
                continue 

            if token_type == 'UNKNOWN':
                msg = f"Неизвестное слово или символ '{token_value}'"
                self.errors.append((msg, token_start, token_end))
                continue

            # Re-classify general 'NAME' tokens as 'IDENTIFIER' so the parser can handle them.
            if token_type == 'NAME':
                token_type = 'IDENTIFIER'

            tokens.append(Token(token_type, token_value, token_start, token_end))

        return tokens, self.errors
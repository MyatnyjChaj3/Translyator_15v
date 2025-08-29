import tkinter as tk
from parser import Parser, format_value
from tkinter import scrolledtext

from lexer import Lexer


class TranslatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("BNF Translator")
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=3)
        master.grid_rowconfigure(1, weight=1)

        self.top_pane = tk.PanedWindow(master, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.top_pane.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # Панель для ввода кода
        self.input_frame = tk.LabelFrame(self.top_pane, text="Пользовательский ввод")
        self.input_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.input_text = scrolledtext.ScrolledText(self.input_frame, wrap=tk.WORD, width=40, height=15, font=('Courier New', 10))
        self.input_text.pack(fill='both', expand=True)
        self.top_pane.add(self.input_frame, stretch="always")

        # Панель для отображения БНФ
        self.bnf_frame = tk.LabelFrame(self.top_pane, text="Формальное описание языка (БНФ)")
        self.bnf_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.bnf_text = scrolledtext.ScrolledText(self.bnf_frame, wrap=tk.WORD, width=40, height=15, font=('Courier New', 10), state=tk.DISABLED)
        self.bnf_text.pack(fill='both', expand=True)
        self.top_pane.add(self.bnf_frame, stretch="always")

        # Обновленное описание БНФ
        formal_description = """Язык = "Start" Множ...Множ Окончание "End"
Множ = "Array" число...число
число = Вещ | Цел | Компл
Окончание = перем "=" прав. часть
Прав. часть = блок1["+" | "-"]...блок1
блок1 = блок2["*" | "/"]...блок2
блок2 = блок3"**"...блок3
блок3 = перем | вещ | "[" прав. часть "]" (n<=2)
перем = буква буква цифра цифра цифра
компл = вещ "," вещ
вещ = цел "." цел
цел = циф...циф
буква = "A" | "B" | ... | "Z"
цифра = "0" | "1" | ... | "7"
"""
        self.bnf_text.config(state=tk.NORMAL)
        self.bnf_text.insert(tk.END, formal_description)
        self.bnf_text.config(state=tk.DISABLED)

        # Панель для вывода результатов и ошибок
        self.output_frame = tk.LabelFrame(master, text="Результат / Ошибки")
        self.output_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        self.output_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, height=10, font=('Courier New', 10), state=tk.DISABLED)
        self.output_text.pack(fill='both', expand=True)

        # Кнопка трансляции
        self.translate_button = tk.Button(master, text="Транслировать", command=self.translate)
        self.translate_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.input_text.tag_configure("error", background="salmon")

    def translate(self):
        """Основная функция, запускающая процесс трансляции."""
        self.clear_output()
        self.clear_highlight()

        input_code = self.input_text.get("1.0", tk.END).strip()

        if not input_code:
            self.display_output("Введите код для трансляции.")
            return

        # 1. Лексический анализ
        lexer = Lexer(input_code)
        tokens, lexer_errors = lexer.tokenize()

        if lexer_errors:
            self.display_output("Обнаружены ошибки лексического анализа:")
            for msg, start, end in lexer_errors:
                self.display_output(f"- {msg}")
                self.highlight_text(start, end)
            return

        # 2. Синтаксический анализ
        parser = Parser(tokens, input_code)
        symbol_table, parser_errors = parser.parse()

        if parser_errors:
            self.display_output("Обнаружена синтаксическая ошибка:")
            # Сортируем ошибки по позиции для корректного отображения
            parser_errors.sort(key=lambda x: x[1])
            for msg, start, end in parser_errors:
                self.display_output(f"- {msg}")
                self.highlight_text(start, end)
            return

        # 3. Вывод результата
        self.display_output("Трансляция успешно завершена.")
        self.display_output("\nРезультат вычислений (восьмеричные значения):")
        if symbol_table:
            for var, value in symbol_table.items():
                self.display_output(f"{var} = {format_value(value)}")
        else:
            self.display_output("Переменные не были объявлены.")

    def display_output(self, message):
        """Отображает сообщение в поле вывода."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(tk.END)

    def clear_output(self):
        """Очищает поле вывода."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)

    def highlight_text(self, start_index, end_index):
        """Подсвечивает текст с ошибкой в поле ввода."""
        start_pos = f"1.0+{start_index}c"
        end_pos = f"1.0+{end_index}c"
        self.input_text.tag_add("error", start_pos, end_pos)

    def clear_highlight(self):
        """Убирает всю подсветку ошибок."""
        self.input_text.tag_remove("error", "1.0", tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    gui = TranslatorGUI(root)
    root.mainloop()
class ColoredPrinter:
    COLOR_CODES = {
        "B$": "\033[30m",  # Black
        "R$": "\033[31m",  # Red
        "G$": "\033[32m",  # Green
        "Y$": "\033[33m",  # Yellow
        "A$": "\033[34m",  # Azure (Blue)
        "M$": "\033[35m",  # Magenta
        "C$": "\033[36m",  # Cyan
        "W$": "\033[37m"   # White
    }
    RESET_CODE = "\033[0m"

    def __init__(self):
        pass

    def _replace_color_codes(self, text):
        for code, color in self.COLOR_CODES.items():
            text = text.replace(code, color)
        return text

    def print(self, *args, sep=' ', end='\n', file=None, flush=False):
        text = sep.join(map(str, args))
        text = self._replace_color_codes(text)
        text += self.RESET_CODE  # Ensure the color is reset at the end
        print(text, sep=sep, end=end, file=file, flush=flush)

# Usage example
# printer = ColoredPrinter()

# printer.print("This is B$black text, R$red text, G$green text.")
# printer.print("Here is Y$yellow text, A$azure text, M$magenta text, C$cyan text, and W$white text.")

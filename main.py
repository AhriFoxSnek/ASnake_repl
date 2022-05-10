execGlobal = globals()
from ASnake import build, ASnakeVersion
from io import StringIO
from contextlib import redirect_stdout

import platform  # temp


debug: bool = False # enables file output of useful info for debugging

OS = platform.system().lower()
if 'windows' in OS:
    OS = 'windows'
    try:
        import curses
    except ModuleNotFoundError:
        print("curses not supported. Please install via something like:\npython -m pip install windows-curses")
        exit()
else:
    import curses

# v temporary
import sys
compileDict = {'CPython': 'Python', 'PyPy': 'PyPy3'}
# ^ temporary

pythonVersion=f"{sys.version_info.major}.{sys.version_info.minor}" # run-time constant

if hasattr(sys, "pyston_version_info"):
    # ^ Pyston dev's suggested this: https://github.com/pyston/pyston/issues/39
    # What scaredy cats!!
    compileTo = 'Pyston'
else:
    compileTo = compileDict[platform.python_implementation()]
del sys, compileDict, platform

# constants
ReplVersion = 'v0.4.2'
PREFIX = ">>> "
PREFIXlen = len(PREFIX)


# check for ASnake as it can't be appended in requirements.txt (for now)
def perform_module_check():
    import sys
    if not 'ASnake' in sys.modules:
        print("Install latest ASnake.py from https://github.com/AhriFoxSnek/ASnake")
        exit()


# for debugging only
def file_out(write_mode, *args):
    with open("streams.txt", write_mode, encoding='utf-8') as f:
        f.write(f"{args}\n")


def get_hint(word):
    if word == "": return ''
    for key, value in lookup.items():
        if key[:len(word)] == word:
            return value
    return ''


def display_hint(stdscr, y: int, x: int, code: str, lastCursorX: int, after_appending: int, hinted: bool, maxX: int):
    if hinted:  # delete last hint
        clear_suggestion(stdscr=stdscr, start=lastCursorX + 1, end=maxX, step=1, y=y)
        stdscr.delch(y, lastCursorX)
        stdscr.move(y, lastCursorX)
    if get_hint(code) == '':
        return False
    for i in range(after_appending, lastCursorX, -1):
        stdscr.delch(y, i)
    if 'windows' == OS:
        color = curses.color_pair(4)
    else:
        color = curses.color_pair(1) | curses.A_DIM
    stdscr.addstr(y, x + len(code.split()[-1][len(code):]), get_hint(code.split()[-1])[len(code):], color)
    stdscr.move(y, x)
    return True


def delete_line(stdscr, start, end, step, y):
    for i in range(start, end, step):
        stdscr.delch(y, i)


def clear_suggestion(stdscr, start, end, step, y):
    delete_line(stdscr, start, end, step, y)
    stdscr.delch(y, start)
    stdscr.move(y, start)

def buildCode(code, variableInformation, metaInformation):
    output = build(code, comment=False, optimize=False, debug=False, compileTo=compileTo,
                   pythonVersion=pythonVersion, enforceTyping=False, variableInformation=variableInformation,
                   outputInternals=True, metaInformation=metaInformation)
    if isinstance(output, str):
        # ASnake Syntax Error
        return (output, variableInformation, metaInformation)
    else:
        if variableInformation != output[2]:
            variableInformation = output[2]
            for var in variableInformation:
                lookup[var] = var
        return (output[0], variableInformation, output[3])


bash_history = []
keyword_list = ('__build_class__', '__debug__', '__doc__', '__import__', '__loader__', '__name__', '__package__',
                '__spec__', 'abs', 'all', 'and', 'any', 'ArithmeticError', 'as', 'ascii', 'assert', 'AssertionError',
                'async', 'AttributeError', 'await', 'BaseException', 'bin', 'BlockingIOError', 'bool', 'break',
                'breakpoint', 'BrokenPipeError', 'BufferError', 'bytearray', 'bytes', 'BytesWarning', 'callable',
                'ChildProcessError', 'chr', 'class', 'classmethod', 'compile', 'complex', 'ConnectionAbortedError',
                'ConnectionError', 'ConnectionRefusedError', 'ConnectionResetError', 'continue', 'copyright', 'credits',
                'def', 'del', 'delattr', 'DeprecationWarning', 'dict', 'dir', 'divmod', 'elif', 'Ellipsis', 'else',
                'enumerate', 'EnvironmentError', 'EOFError', 'eval', 'except', 'Exception', 'exec', 'exit', 'False',
                'FileExistsError', 'FileNotFoundError', 'filter', 'finally', 'float', 'FloatingPointError', 'for',
                'format', 'from', 'frozenset', 'FutureWarning', 'GeneratorExit', 'getattr', 'global', 'globals',
                'hasattr', 'hash', 'help', 'hex', 'id', 'if', 'import', 'ImportError', 'ImportWarning', 'in',
                'IndentationError', 'IndexError', 'input', 'int', 'InterruptedError', 'IOError', 'is',
                'IsADirectoryError', 'isinstance', 'issubclass', 'iter', 'KeyboardInterrupt', 'KeyError', 'lambda',
                'len', 'license', 'list', 'locals', 'LookupError', 'map', 'max', 'MemoryError', 'memoryview', 'min',
                'ModuleNotFoundError', 'NameError', 'next', 'None', 'nonlocal', 'not', 'NotADirectoryError',
                'NotImplemented', 'NotImplementedError', 'object', 'oct', 'open', 'or', 'ord', 'OSError',
                'OverflowError', 'pass', 'PendingDeprecationWarning', 'PermissionError', 'pow', 'print',
                'ProcessLookupError', 'property', 'quit', 'raise', 'range', 'RecursionError', 'ReferenceError', 'repr',
                'ResourceWarning', 'return', 'reversed', 'round', 'RuntimeError', 'RuntimeWarning', 'set', 'setattr',
                'slice', 'sorted', 'staticmethod', 'StopAsyncIteration', 'StopIteration', 'str', 'sum', 'super',
                'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'TimeoutError', 'True', 'try',
                'tuple', 'type', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError',
                'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning', 'ValueError', 'vars',
                'Warning', 'while', 'with', 'yield', 'ZeroDivisionError', 'zip',

                # ASnake keywords
                'case', 'do', 'does', 'end', 'equals', 'greater', 'less', 'loop', 'minus', 'nothing', 'of', 'plus',
                'power', 'remainder', 'than', 'then', 'times', 'until',

                # Environment
                'ASnakeVersion','build','OS','pythonVersion'
                )
lookup = {}
for name in keyword_list:
    lookup[name] = name
del keyword_list


def main(stdscr):
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)  # for usual text
    curses.init_pair(2, curses.COLOR_CYAN, -1)  # for pretty prefix
    curses.init_pair(3, curses.COLOR_RED, -1) # for scary error
    if 'windows' == OS:
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.echo()
    stdout = StringIO()

    # v debug vars v
    extra = ''
    debugFileOut=False

    after_appending = 0
    lastCursorX: int = 4
    hinted: bool = False

    code = ''
    variableInformation = {}
    metaInformation = []
    codePosition = 0
    stdscr.addstr(f"ASnake {ASnakeVersion} \nRepl {ReplVersion}\n\n")
    stdscr.addstr(PREFIX, curses.color_pair(2))

    history_idx = 0
    while True:
        c = stdscr.getch()
        codeLength = len(code)
        # notetoself: x and y are cursor position
        y, x = stdscr.getyx()
        height, width = stdscr.getmaxyx()

        if codePosition > codeLength:
            codePosition = codeLength
        elif codePosition < 0:
            codePosition = 0

        if c == curses.KEY_LEFT:
            debugFileOut = True
            if not x < PREFIXlen+1:
                stdscr.move(y, x - 1)
                if codePosition <= codeLength and x - PREFIXlen <= codePosition:
                    codePosition -= 1

        elif c == 546: # CTRL_LEFT
            debugFileOut = True
            if not x < PREFIXlen+1 and codePosition > 0:
                while code[codePosition-1] == ' ':
                    if codePosition == 0:
                        break
                    codePosition -= 1
                while code[codePosition-1] != ' ':
                    if codePosition == 0:
                        break
                    codePosition -= 1
                stdscr.move(y, PREFIXlen+codePosition)

        elif c == 561: # CTRL_RIGHT
            debugFileOut = True
            if codePosition < codeLength:
                while code[codePosition-1] == ' ':
                    codePosition += 1
                    if codePosition > codeLength:
                        codePosition = codeLength
                        break
                while code[codePosition-1] != ' ':
                    codePosition += 1
                    if codePosition > codeLength:
                        codePosition=codeLength
                        break
                stdscr.move(y, PREFIXlen+codePosition)

        elif c == curses.KEY_RIGHT:
            debugFileOut = True
            if codePosition < codeLength:
                stdscr.addstr(code[codePosition])
                codePosition += 1
            stdscr.move(y, x + 1)

        # todo -> bash history
        elif c == curses.KEY_UP:
            debugFileOut = True
            if history_idx > 0:
                # earlier history
                if history_idx > len(bash_history):
                    history_idx = len(bash_history)
                history_idx -= 1
                delete_line(stdscr=stdscr, start=x, end=PREFIXlen - 1, step=-1, y=y)
                stdscr.addstr(bash_history[history_idx])
                code = bash_history[history_idx]
                codePosition += len(bash_history[history_idx])
            else:
                history_idx = 0

        elif c == curses.KEY_DOWN:
            debugFileOut = True
            if history_idx < len(bash_history) - 1:
                # later history
                history_idx += 1
                delete_line(stdscr=stdscr, start=x, end=PREFIXlen - 1, step=-1, y=y)
                stdscr.addstr(bash_history[history_idx])
                code = bash_history[history_idx]
                codePosition += len(bash_history[history_idx])
            else:
                # the most down should be blank
                history_idx = len(bash_history)
                delete_line(stdscr=stdscr, start=x, end=PREFIXlen - 1, step=-1, y=y)

        # tab -> for auto-complete feature
        elif c == ord('\t'):
            debugFileOut = True
            # call get_hint function to return the word which fits :n-index of `code` variable
            after_appending = x + 1
            codeSplit = code.split()
            if codeSplit:
                autocomplete: str = get_hint(codeSplit[-1])
                if autocomplete != '':
                    # autocomplete found
                    stdscr.move(y, codePosition + PREFIXlen - len(codeSplit[-1]))

                    stdscr.addstr(autocomplete)
                    code = ' '.join(codeSplit[:-1]) + (' ' if len(codeSplit) > 1 else '') + autocomplete
                    codePosition += len(autocomplete) - len(codeSplit[-1])
                else:
                    # no autocomplete found
                    if codePosition != codeLength:
                        # not at end of line
                        stdscr.move(y, x - 1)
                        stdscr.addstr(code[codePosition:])
                    # move to end of line
                    stdscr.move(y, len(code) + PREFIXlen)
            elif codePosition == 0:
                # at start of line with nothing
                stdscr.move(y, PREFIXlen)

        elif c in {curses.KEY_BACKSPACE, 127, 8}:
            debugFileOut = True
            if not x < 4:
                clear_suggestion(stdscr=stdscr, start=lastCursorX, end=width, step=1, y=y)
                stdscr.delch(y, x)

                if 0 < codePosition < len(code) - 1:
                    tmpStart = codePosition - 1 if codePosition - 1 > 0 else 0
                    code = code[:tmpStart] + code[codePosition:]
                else:
                    code = code[:-1]
                codePosition -= 1
                display_hint(stdscr, y, x, code, 0, 0, False, 0)
            else:
                stdscr.move(y, x + 1)
            if code == '' and x <= 4:
                # if no characters, clear suggestion
                clear_suggestion(stdscr=stdscr, start=4, end=width, step=1, y=y)

        elif c in {curses.KEY_ENTER, 10, 13}:
            debugFileOut = True
            if y >= height - 1:
                stdscr.clear()
                stdscr.refresh()
            else:
                # evaluate the line/block

                history_idx += 2
                bash_history.append(code)
                delete_line(stdscr=stdscr, start=stdscr.getmaxyx()[0], end=PREFIXlen + codePosition - 1, step=-1, y=y)
                if 'windows' == OS:
                    stdscr.move(y, 0)
                else:
                    stdscr.move(y + 1, 0)
                compiledCode, variableInformation, metaInformation = buildCode(code, variableInformation,
                                                                               metaInformation)
                with redirect_stdout(stdout):
                    try:
                        exec(compiledCode, execGlobal)
                    except Exception as e:
                        error = compileTo + ' ' + e.__class__.__name__ + ':\n' + str(e)
                        stdscr.addstr(error, curses.color_pair(3))
                        stdscr.move(y + error.count('\n') + 2, 0)

                if compiledCode.startswith(f'# ASnake {ASnakeVersion} ERROR'):
                    ASError = True
                else:
                    ASError = False

                output = list(stdout.getvalue())
                for i in range(len(output)):
                    y, _ = stdscr.getyx()
                    if y >= height - 1:
                        stdscr.clear()
                        stdscr.move(0, 0)
                    stdscr.addstr(f"{output[i]}", curses.color_pair(3) if ASError else curses.color_pair(1))

                stdout = StringIO()
                stdscr.addstr(PREFIX, curses.color_pair(2))
                code = ''
                codePosition = 0
                stdscr.refresh()

        else:
            debugFileOut = True
            if codePosition == len(code):
                code += chr(c)
                codePosition += 1
                lastCursorX = x
                if code[-1] != ' ':
                    hinted = display_hint(stdscr, y, x, code.split()[-1], lastCursorX, after_appending, hinted, width)
                else:
                    # if a space is done on a suggestion, clear the suggestion
                    clear_suggestion(stdscr=stdscr, start=lastCursorX, end=width, step=1, y=y)
            else:
                if codePosition == 1:
                    code = chr(c) + code[codePosition:]
                else:
                    code = code[:codePosition] + chr(c) + code[codePosition:]
                    codePosition += 1
                delete_line(stdscr=stdscr, start=x - 1 + len(code[codePosition:]), end=x - 1, step=-1, y=y)
                stdscr.addstr(code[codePosition:])
                stdscr.move(y, x)
                stdscr.refresh()

        if debug and debugFileOut:
            file_out('w', code,f"{codePosition}/{len(code)} x={x} y={y} bi={history_idx}",extra)


if __name__ == "__main__":
    perform_module_check()
    curses.wrapper(main)


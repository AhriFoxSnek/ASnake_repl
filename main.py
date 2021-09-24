execGlobal = globals()
from enum import auto
from os import altsep
from re import L
from time import sleep
from ASnake import build, execPy, ASnakeVersion
import subprocess
import io
from contextlib import redirect_stdout

import platform
if 'windows' in platform.system().lower():
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

if hasattr(sys, "pyston_version_info"):
    # ^ Pyston dev's suggested this: https://github.com/pyston/pyston/issues/39
    # What scaredy cats!!
    compileTo = 'Pyston'
else:
    compileTo = compileDict[platform.python_implementation()]
del sys, compileDict, platform

# constants
ReplVersion = 'v0.3.0'
PREFIX = ">>> "
PREFIXlen = len(PREFIX)


# for debugging only
def file_out(write_mode, *args):
    with open("streams.txt", write_mode, encoding='utf-8') as f:
        f.write(f"{args}\n")


def get_hint(word):
    if word == "": return ''
    for key,value in lookup.items():
        if key[:len(word)] == word:
            return value
    return ''

def display_hint(stdscr, y: int, x: int, code: str, lastCursorX: int, after_appending: int):
    if get_hint(code) == '': return
    for i in range(after_appending, lastCursorX, -1):
        stdscr.delch(y, i)
    after_appending = x+len(get_hint(code).split()[-1][len(code):])
    file_out("w", after_appending, lastCursorX)
    stdscr.addstr(y, x+len(code.split()[-1][len(code):]), get_hint(code.split()[-1])[len(code):], curses.color_pair(1) | curses.A_DIM)
    stdscr.move(y, x)

def buildCode(code,variableInformation,metaInformation):
    output = build(code, comment=False, optimize=False, debug=False, compileTo=compileTo,
                   pythonVersion=3.9, enforceTyping=False, variableInformation=variableInformation,
                   outputInternals=True, metaInformation=metaInformation)
    if isinstance(output,str):
        # ASnake Syntax Error
        return (output, variableInformation)
    else:
        if variableInformation != output[2]:
            variableInformation = output[2]
            for var in variableInformation:
                lookup[var]=var
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

                #ASnake keywords
                'case', 'do', 'does', 'end', 'equals', 'greater', 'less', 'loop', 'minus', 'nothing', 'of', 'plus',
                'power', 'remainder', 'than', 'then', 'times', 'until'
                )
lookup = {}
for name in keyword_list:
    lookup[name]=name
del keyword_list

def main(stdscr):
    # stdscr.nodelay(10)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1) # for usual text
    curses.init_pair(2, curses.COLOR_CYAN, -1) # for pretty prefix
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.echo()
    stdout = io.StringIO()

    extra = ''  # debug var

    after_appending = 0
    lastCursorX = 0

    code = ''
    variableInformation = {}
    metaInformation = []
    codePosition = 0
    stdscr.addstr(f"ASnake {ASnakeVersion} \nRepl {ReplVersion}\n\n")
    stdscr.addstr(PREFIX, curses.color_pair(2))

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
            if not x < 5:
                stdscr.move(y, x - 1)
                if codePosition <= codeLength and x - PREFIXlen <= codePosition:
                    codePosition -= 1

        elif c == curses.KEY_RIGHT:
            if codePosition < codeLength:
                stdscr.addstr(code[codePosition])
                codePosition += 1
            stdscr.move(y, x + 1)

        # todo -> bash history
        elif c == curses.KEY_UP:
            pass

        # tab -> for auto-complete feature
        elif c == ord('\t'):
            # call get_hint function to return the word which fits :n-index of `code` variable
            # file_out("a", f"from tab {x}")
            after_appending = x+1
            codeSplit = code.split()
            if codeSplit:
                autocomplete: str = get_hint(codeSplit[-1])
                if autocomplete != '':
                    # autocomplete found
                    stdscr.move(y, codePosition+PREFIXlen-len(codeSplit[-1]))

                    stdscr.addstr(autocomplete)
                    code = ' '.join(codeSplit[:-1]) + (' ' if len(codeSplit)>1 else '') + autocomplete
                    codePosition += len(autocomplete)-len(codeSplit[-1])
                else:
                    # no autocomplete found
                    if codePosition != codeLength:
                        # not at end of line
                        stdscr.move(y,x-1)
                        stdscr.addstr(code[codePosition:])
                    # move to end of line
                    stdscr.move(y, len(code)+PREFIXlen)
            elif codePosition == 0:
                # at start of line with nothing
                stdscr.move(y, PREFIXlen)

        elif c in {curses.KEY_BACKSPACE, 127}:
            if not x < 4:
                stdscr.delch(y, x)
                if 0 < codePosition < len(code) - 1:
                    tmpStart = codePosition - 1 if codePosition - 1 > 0 else 0
                    code = code[:tmpStart] + code[codePosition:]
                else:
                    code = code[:-1]
                codePosition -= 1
                # file_out("a", code)
            else:
                stdscr.move(y, x + 1)

        elif c in {curses.KEY_ENTER, 10, 13}:
            if y >= height - 1:
                stdscr.clear()
                stdscr.refresh()
            else:
                for xx in range(stdscr.getmaxyx()[0],PREFIXlen+codePosition-1,-1):
                    # gets rid of auto-complete-suggestion when entering a new line
                    stdscr.delch(y, xx)

                stdscr.move(y + 1, 0)
                compiledCode, variableInformation, metaInformation = buildCode(code,variableInformation,metaInformation)
                #extra=metaInformation
                with redirect_stdout(stdout):
                    try:
                        exec(compiledCode, execGlobal)
                    except Exception as e:
                        error = compileTo+' '+e.__class__.__name__+':\n'+str(e)
                        stdscr.addstr(error, curses.color_pair(3))
                        stdscr.move(y + error.count('\n') + 2, 0)

                output = stdout.getvalue()
                # file_out("w", output.split("\n"), len(output.split("\n")))
                out_arr = output.splitlines()

                for i in range(len(out_arr)):
                    y, _ = stdscr.getyx()
                    if y >= height - 1:
                        stdscr.clear()
                        stdscr.addstr(f"{out_arr[i]}\n")
                    else:
                        stdscr.addstr(f"{out_arr[i]}\n")
                    # file_out("a", out_arr[i], y)

                stdout = io.StringIO()
                stdscr.addstr(PREFIX, curses.color_pair(2))
                # file_out("w", bash_history)
                code = ''
                codePosition = 0
                stdscr.refresh()

        else:
            if codePosition == len(code):
                code += chr(c)
                codePosition += 1
                # file_out("w", get_hint(code.split()[-1]))
                lastCursorX = x
                display_hint(stdscr, y, x, code.split()[-1],lastCursorX,after_appending)
            else:
                if codePosition == 1:
                    code = chr(c) + code[codePosition:]
                else:
                    code = code[:codePosition] + chr(c) + code[codePosition:]
                    codePosition += 1

                for xx in range(x - 1 + len(code[codePosition:]), x - 1, -1):
                    stdscr.delch(y, xx)
                stdscr.addstr(code[codePosition:])
                stdscr.move(y, x)
                stdscr.refresh()

        #file_out('w', code,f"{codePosition}/{len(code)} x={x} y={y}",extra)

    stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)


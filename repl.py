try:
    from ASnake import build, ASnakeVersion
except ImportError:
    from ASnake.ASnake import build, ASnakeVersion
except ModuleNotFoundError:
    print("ASnake not found. Install latest ASnake.py from https://github.com/AhriFoxSnek/ASnake")
    exit()
from os import listdir, remove, getcwd, environ, kill
from subprocess import Popen, PIPE, DEVNULL, call
from time import sleep
from re import compile as re_compile
from re import escape  as re_escape

# v temporary
import platform
import sys
compileDict = {'CPython': 'Python', 'PyPy': 'PyPy3'}
# ^ temporary
pyCall='"'+sys.executable+'"'
OS = platform.system().lower()
noDill=False
if 'windows' in OS:
    OS = 'windows'
    environ['PYTHONIOENCODING'] = 'UTF8'
    try:
        import curses
    except ModuleNotFoundError:
        print(f"curses not supported. windows-curses is mandatory.\nPlease install via:\n\t{pyCall[1:-1]} -m pip install windows-curses")
        exit()
    try:
        import dill
        del dill
    except ModuleNotFoundError:
        print(f"dill is not installed. dill is mandatory.\nPlease install via:\n\t{pyCall[1:-1]} -m pip install dill")
        exit()
    from signal import SIGINT as stopExecution
    from signal import signal
else:
    try:
        import curses
    except ModuleNotFoundError:
        print(f"curses is not installed. curses is mandatory.\nPlease install via:\n\t{pyCall[1:-1]} -m pip install curses")
        exit()
    try:
        import dill
        del dill
    except ModuleNotFoundError:
        """
        print(f"dill is not installed. dill is optional.\nYou can install it via:\n\t{pyCall[1:-1]} -m pip install dill")
        tmp=input("You can continue without it. Your session will not be saved after exit. Continue? Y/n: ")
        if 'n' in tmp.lower():
            exit()
        else: noDill=True
        """
        noDill=True 
    from signal import SIGINT as stopExecution


pythonVersion=f"{sys.version_info.major}.{sys.version_info.minor}" # run-time constant

if hasattr(sys, "pyston_version_info"):
    # ^ Pyston dev's suggested this: https://github.com/pyston/pyston/issues/39
    # What scaredy cats!!
    compileTo = 'Pyston'
else:
    compileTo = compileDict[platform.python_implementation()]
del sys, compileDict, platform

# constants
ReplVersion = 'v0.12.0'
PREFIX = ">>> "
PREFIXlen = len(PREFIX)
INDENT = "... "
INDENTlen = len(INDENT)
SPACE = '  '
SPACElen = len(SPACE)
checkIfIndent   = re_compile('^(?: |\t)*(?:if|elif|case|of|else|while|def) .+(:|;| do| then) *$').search
exitIndent      = re_compile(f'\n+(?:{SPACE})*$').search
deIndent        = re_compile(f'\n{SPACE}+').findall


# for debugging only
def file_out(write_mode, *args):
    with open("streams.txt", write_mode, encoding='utf-8') as f:
        f.write(f"{args}\n")

trimSuggestion = re_compile(f"[{re_escape(' ()*+-/,=&^%$#@')}]+")
def get_last_substring(s, return_last=True, return_index=False):
    matches = list(trimSuggestion.finditer(s))
    if not matches:
        if return_index:
            return 0
        return ''
    last_index = matches[-1].end() - 1
    if return_index:
        return last_index
    if return_last:
        return s[last_index + 1:]
    return s[:last_index + 1]

def get_hint(word,seperateBasedOnCharacter=True):
    if not word: return ''
    if seperateBasedOnCharacter:
        tmp=get_last_substring(word)
        if tmp: word=tmp
    for key, value in lookup.items():
        if key[:len(word)] == word:
            return value
    return ''


def delete_line(stdscr, start, end, step, y):
    for i in range(start, end, step):
        stdscr.delch(y, i)

def clear_suggestion(stdscr, start, end, step, y):
    delete_line(stdscr, start, end, step, y)
    stdscr.delch(y, start)
    stdscr.move( y, start)

def display_hint(stdscr, y: int, x: int, code: str, lastCursorX: int, after_appending: int, hinted: bool, maxX: int):
    if hinted:  # delete last hint
        clear_suggestion(stdscr=stdscr, start=lastCursorX + 2, end=maxX, step=1, y=y)
        stdscr.delch(y, lastCursorX+1)
        stdscr.move(y, lastCursorX+1)
    if not code or not get_hint(code.split()[-1]):
        return False
    for i in range(after_appending, lastCursorX+1, -1):
        stdscr.delch(y, i)
    if 'windows' == OS:
        color = curses.color_pair(4)
    else:
        color = curses.color_pair(1) | curses.A_DIM
    stdscr.addstr(y, (x+1) + len(code.split()[-1][len(code):]), get_hint(code.split()[-1])[abs(len(get_last_substring(code,False))-len(code)):], color)
    stdscr.move(y, x+1)
    return True
    

def buildCode(code, variableInformation, metaInformation):
    output = build(code, comment=False, optimize=False, debug=False, compileTo=compileTo,
                   pythonVersion=pythonVersion, enforceTyping=False, variableInformation=variableInformation,
                   outputInternals=True, metaInformation=metaInformation)
    if isinstance(output, str):
        # ASnake Syntax Error
        return (output, variableInformation, metaInformation)
    else:
        variableInformation = output[2]
        for var in variableInformation:
            lookup[var] = var
        return (output[0], variableInformation, output[3])


bash_history = []
stopCharacters = set(" .()*+-/,'\"=&^%$#@{}")
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
                'Warning', 'while', 'with', 'yield', 'ZeroDivisionError', 'zip', 'case', 'match',

                # ASnake keywords
                'do', 'does', 'end', 'equals', 'greater', 'less', 'loop', 'minus', 'nothing', 'of', 'plus',
                'power', 'remainder', 'than', 'then', 'times', 'divide', 'rdivide', 'round divide', 'round divide by',
                'modulo', 'remainder', 'are', 'arent', 'each of', 'const', 'constant', 'pipe', 'into', 'to', 'exponent',
                'cdoes', 'cdef',

                # Environment
                'listdir','remove','sleep'
                )
lookup = {}
for name in keyword_list:
    lookup[name] = name
del keyword_list

if noDill:
    runFile='executionEnvironmentNoDill.py'
else:
    runFile='executionEnvironment.py'
from time import sleep
def main(stdscr):
    isWindows = True if OS == 'windows' else False
    child = Popen(f'{pyCall} -u {runFile}', stdout=PIPE, cwd=getcwd(), shell=False if isWindows else True)
    def exitRoutine():
        nonlocal child
        if 'ASnakeREPLCommand.txt' in listdir():
            try:
                remove('ASnakeREPLCommand.txt')
            except:
                pass
            try:
                child.terminate()
            except:
                pass
        exit()
    
    # preallocated functions
    readChildStdout = child.stdout.read
    childPoll = child.poll
    stdscr_getch=stdscr.getch
    stdscr_getyx=stdscr.getyx
    stdscr_getmaxyx=stdscr.getmaxyx

    # character variables
    exitByte = chr(999999)
    errorByte = chr(999998)
    KEY_TAB = ord('\t')
    KEY_BACKSPACE = {curses.KEY_BACKSPACE, 127, 8, 330}
    KEY_ENTER = {curses.KEY_ENTER, 10, 13}
    CTRL_LEFT = {ord('Ȧ'),ord('Ȫ'),ord('ȫ'), 564, 546}
    CTRL_RIGHT = {ord('ȵ'), ord('ȹ'), ord('ŋ'), ord('ą'), 561}
    CTRL_W = ord(b'\x17')
    # shift left 393 ; shift right 402
    # alt tab 27
    # backslash 92
    
    # colors
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)  # for usual text
    curses.init_pair(2, curses.COLOR_CYAN, -1)  # for pretty prefix
    curses.init_pair(3, curses.COLOR_RED, -1) # for scary error
    curses.init_pair(5, curses.COLOR_GREEN, -1) # for strings
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # for numbers
    if isWindows:
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.noecho()
    
    # vv debug vars vv
    debug: bool = False  # enables file output of useful info for debugging
    extra = ''
    debugFileOut=False
    debugTryCommands=[]
    #debugTryCommands=["list frames = ['/','-','\\\\','|']"] + [10, "from time import sleep", 10, 'while 0 do loop frames f do f ; sleep(0.2)',10,curses.KEY_UP]
    #debugTryCommands=['"f"',curses.KEY_LEFT,"aaaaa",curses.KEY_LEFT,curses.KEY_LEFT,curses.KEY_LEFT,'"','"',curses.KEY_LEFT,'+']
    #debugTryCommands = ['if 1 do',list(KEY_ENTER)[1],'1',curses.KEY_UP,curses.KEY_DOWN,'2',list(KEY_ENTER)[1],'1',curses.KEY_UP,'3']
    #debugTryCommands = ['if 1 do',list(KEY_ENTER)[1],list(KEY_ENTER)[1],'12',list(KEY_ENTER)[1],curses.KEY_UP,curses.KEY_UP,' ',chr(575),'2',chr(534),'3']
    #debugTryCommands = ['if True do', list(KEY_ENTER)[1], '12', list(KEY_ENTER)[1], list(KEY_ENTER)[1], curses.KEY_UP, curses.KEY_UP, list(KEY_ENTER)[1],curses.KEY_UP, curses.KEY_DOWN]
    # ^ does command on startup to test a specific case
    debugTryCommands = [ord(char) if isinstance(item, str) else item for item in debugTryCommands for char in (str(item) if isinstance(item, str) else [item])]
    # ^ auto converts for understandable format for the REPL
    # -- debug var end --

    # v normal vars v
    after_appending = 0
    lastCursorX: int = 4
    hinted: bool = False
    firstLine: bool = True
    inIndent: bool = False
    currentIndent: int = 0
    inString = False # only values: False 34 39

    code = ''
    variableInformation = {}
    metaInformation = []
    codePosition = 0
    preface = f"ASnake {ASnakeVersion} on {compileTo} v{pythonVersion} \nRepl {ReplVersion}\n\n"
    prefaceLEN = preface.count('\n')
    
    def skipToCharacter(stdscr, x, y, stopCharacters=stopCharacters, direction='left', delete=False):
        nonlocal code, codePosition #, extra
        tmpPosition = 0 if direction == 'left' else len(code)+1

        i = 1 if direction == 'left' else -1
        # these prevent overflow
        if direction == 'right' and codePosition-i >= len(code)-1: return
        elif direction == 'left' and codePosition <= 0: return
        # skip multiple
        try:
            while code[codePosition - i] in stopCharacters:
                if direction == 'left':
                    codePosition -= 1
                elif direction == 'right':
                    codePosition += 1
                i += 1 if direction == 'left' else -1
                if not (0 <= codePosition-1 <= len(code)-1) : break
        except IndexError: return
        i = 1 if direction == 'left' else -1

        if direction == 'left':
            theRange = range(codePosition, 1, -1)
        elif direction == 'right':
            theRange = range(codePosition, len(code)-1, 1)
        for char in theRange:
            if code[char - i] in stopCharacters:
                if code[char - i] == ' ':
                    try:
                        if code[char - i*2] != ' ':
                            pass
                        else: continue
                    except IndexError: pass
                tmpPosition = char ; break
        if delete: code = code[:tmpPosition]
        if tmpPosition > len(code): tmpPosition-=1
        codePosition = tmpPosition

        if codePosition <= width-PREFIXlen:
            tmpY = linesStartingY
            tmpPosition = tmpPosition + PREFIXlen - i
        else:
            tmpY = (codePosition // width)
            tmpPosition = (codePosition - (width*tmpY))
            if y == linesStartingY: tmpPosition += PREFIXlen
            if direction == 'right': tmpY += y
            else:  tmpY += prefaceLEN
        if delete:
            delete_line(stdscr=stdscr, start=x, end=tmpPosition, step=-1, y=y)
        stdscr.move(tmpY, tmpPosition-1 if direction == 'right' else tmpPosition+1)

    def redraw(stdscr):
        nonlocal x,y
        delete_line(stdscr=stdscr, start=PREFIXlen, end=width, step=1, y=linesStartingY)
        for yy in range(y + 1, height):
            delete_line(stdscr=stdscr, start=0, end=width, step=1, y=yy)
        yTMP = linesStartingY
        xTMP = PREFIXlen
        scrollWhenYOverflow(yTMP, xTMP)
        stdscr.move(yTMP, xTMP)
        lastChar=False ; tmpInString=False
        for character in code:
            tmpInString = handleSyntaxHighlighting(ord(character),ord(lastChar) if lastChar else False,(yTMP,xTMP),tmpInString=tmpInString)
            xTMP += 1
            if xTMP >= width or character == '\n':
                xTMP = 0; yTMP += 1
                if inIndent and not tmpInString and character == '\n':
                    stdscr.addstr(INDENT, curses.color_pair(2))
                    xTMP = INDENTlen
            stdscr.move(yTMP, xTMP)
            lastChar = character

    def bigClear(customStartingY=False):
        if customStartingY:
            startingY=customStartingY
        else:
            startingY=linesStartingY
        for _y in range(height - 1, startingY, -1):
            for _ in range(height - startingY + 3):
                delete_line(stdscr=stdscr, start=0, end=width, step=1, y=_y)
        for _ in range(y - startingY + 2):
            delete_line(stdscr=stdscr, start=PREFIXlen, end=width, step=1, y=startingY)
        stdscr.move(startingY, PREFIXlen)

    def handleSyntaxHighlighting(c,lastChar=False,customYX=(False,False), tmpInString=False):
        #nonlocal extra
        # expects one character, in ord()
        tmpY=customYX[0] if customYX[1] else y
        tmpX=customYX[1] if customYX[1] else x

        GREEN = curses.color_pair(5)
        MAGENTA = curses.color_pair(6)
        RED = curses.color_pair(3)

        charC=chr(c)
        if lastChar: lastCharC=chr(lastChar)
        if c in {34,39}: # string quotes
            tmpColor = GREEN
            if lastChar:
                if lastCharC in 'frb' and customYX[0]:
                    stdscr.move(tmpY, tmpX-1)
                    stdscr.addstr(chr(lastChar), GREEN)
                elif lastCharC == '\\': tmpColor=RED
            if not tmpInString:
                tmpInString = c
            elif c == tmpInString and not (lastChar and lastCharC == '\\'):
                tmpInString = False
            stdscr.addstr(charC, tmpColor)
        elif tmpInString:                 
            if charC == '\\':  
                    if (lastChar and lastCharC == '\\') and customYX: 
                          stdscr.move(tmpY, tmpX-1)
                          stdscr.addstr(charC, GREEN)
                          stdscr.addstr(charC, GREEN)  
                    else: stdscr.addstr(charC, RED) 
            else:         stdscr.addstr(charC, GREEN)
        elif charC in "0123456789" and ((lastChar and lastCharC in "0123456789 .()*+-/,=&^%$#@{}") or not lastChar):
            if lastChar and lastCharC == '.':
                stdscr.move(tmpY, tmpX-1)
                stdscr.addstr('.', MAGENTA)
            stdscr.addstr(charC, MAGENTA)
        else:
            stdscr.addstr(charC)
        return tmpInString

    def syntaxHighlightString(theString, lastChar=False, customYX=(False, False)):
        # a loop wrapper for handleSyntaxHighlighting
        tmpInString = inString
        tmpLastChar = lastChar if lastChar else False 
        tmpY, tmpX = customYX
        for char in theString:
            tmpInString = handleSyntaxHighlighting(ord(char), lastChar=tmpLastChar, customYX=(tmpY,tmpX), tmpInString=tmpInString)
            tmpLastChar = ord(char)
            tmpX+=1
            if tmpX > width: 
                if tmpY < height: tmpY+=1
                tmpX=PREFIXlen

    def scrollWhenYOverflow(customY=False, customX=False):
        theY = customY if customY else y+1
        theX = customX if customX else 0
        if theY >= height:
            stdscr.scroll(1)
            stdscr.move(height-1, 0)
        else:
            stdscr.move(theY, theX)
            

    # setup
    stdscr.scrollok(True)
    stdscr.addstr(preface)
    stdscr.addstr(PREFIX, curses.color_pair(2))
    
    linesStartingY = prefaceLEN
    history_idx = 0
    while True: # begin the REPL
        if childPoll() == 0: exitRoutine()
        if debug and debugTryCommands:
            c = debugTryCommands.pop(0)
        else:
            c = stdscr_getch()
        chrC = chr(c)
        codeLength = len(code)
        # notetoself: x and y are cursor position
        y, x = stdscr_getyx()
        height, width = stdscr_getmaxyx()

        if codePosition > codeLength:
            codePosition = codeLength
        elif codePosition < 0:
            codePosition = 0
        
        if c == curses.KEY_LEFT:
            debugFileOut = True
            if hinted:
                hinted=False
                clear_suggestion(stdscr=stdscr, start=lastCursorX+1, end=width, step=1, y=y)
            if not x < PREFIXlen+1 or y > linesStartingY:
                if x == 0:
                    y-=1 ; x=width
                stdscr.move(y, x - 1)
                codePosition -= 1
                if   code[:codePosition].count('"') % 2 == 1: inString = ord('"')
                elif code[:codePosition].count("'") % 2 == 1: inString = ord("'")
                if codePosition != codeLength and code[-1] == ' ': code=code[:-1]
            else: inString=False
                

        elif c == curses.KEY_RIGHT and codePosition != codeLength:
            debugFileOut = True
            if hinted:
                if x+1 < width: stdscr.delch(y, x+1)
                hinted=False
                clear_suggestion(stdscr=stdscr, start=lastCursorX+1, end=width, step=1, y=y)
            if codePosition+1 > codeLength:
                code+=' '
            codePosition += 1
            if x+1 >= width: stdscr.move(y + 1, 0)
            else: stdscr.move(y, x + 1)


        elif c == curses.KEY_UP:
            debugFileOut = True
            if inIndent and y > linesStartingY: # regular going up for editing when multiline
              stdscr.move(y - 1, x)
              
              L = code.split('\n') ; s = i = 0
              for i, ln in enumerate(L):
                  if codePosition <= s + len(ln): break
                  s += len(ln) + 1
              codePosition = 0 if i == 0 else sum(len(xx) + 1 for xx in L[:i-1]) + min((codePosition - s), len(L[i-1]))
              del L, s, i
              
            elif bash_history:
                # earlier history
                if history_idx <= len(bash_history):
                    history_idx -= 1
                if history_idx < 0: history_idx=0
                tmpNLSpace = '\n'+SPACE
                if inIndent:
                    if code.count(tmpNLSpace) > 0 and code.split(tmpNLSpace)[-1]:
                        code = ''.join(['\n'+SPACE+_ for _ in code.split(tmpNLSpace)[:-1]])[len(tmpNLSpace):]+'\n'+(SPACE*currentIndent)
                    code += bash_history[history_idx]
                else:
                    code  = bash_history[history_idx]
                    if y == linesStartingY and checkIfIndent(code) == None: inIndent = False

                if y > linesStartingY: # when an entry is multiline, clear the heck out of everything
                    bigClear()
                else:
                    delete_line(stdscr=stdscr, start=x, end=PREFIXlen - 1, step=-1, y=y)
                if code.count(tmpNLSpace) > 0:
                    tmpFirstLine=True
                    #linesStartingY=y
                    for nl in code.split(tmpNLSpace):
                        if not tmpFirstLine:
                            stdscr.addstr('\n'+INDENT+SPACE, curses.color_pair(2))
                        syntaxHighlightString(nl)
                        if tmpFirstLine: tmpFirstLine = False; inIndent = True
                    codePosition += len(bash_history[history_idx].replace('\n',''))

                else:
                    syntaxHighlightString(bash_history[history_idx], customYX=(y,PREFIXlen))
                    codePosition += len(bash_history[history_idx])

        elif c == curses.KEY_DOWN:
            debugFileOut = True
            if inIndent and y < height: # regular going down for editing when multiline
              stdscr.move(y + 1, x)
              codePosition*=y+1
            elif history_idx < len(bash_history) - 1:
                # later history
                history_idx += 1
                if y > linesStartingY: # when an entry is multiline, clear the heck out of everything
                    bigClear(y)
                else:
                    delete_line(stdscr=stdscr, start=PREFIXlen, end=width - 1, step=1, y=linesStartingY)
                    stdscr.move(linesStartingY, prefaceLEN+1)
                syntaxHighlightString(bash_history[history_idx])
                if inIndent:
                    tmpNLSpace = '\n' + SPACE
                    if code.count(tmpNLSpace) > 0 and code.split(tmpNLSpace)[-1]:
                        code = ''.join(['\n'+SPACE+_ for _ in code.split(tmpNLSpace)[:-1]])[len(tmpNLSpace):]+'\n'+(SPACE*currentIndent)
                    code += bash_history[history_idx]
                else:
                    code = bash_history[history_idx]
                codePosition += len(bash_history[history_idx])
            else:
                # the most down should be blank
                code = '' ; codePosition=0
                history_idx = len(bash_history)
                bigClear()
                delete_line(stdscr=stdscr, start=width-1, end=PREFIXlen-1, step=-1, y=linesStartingY)

        # tab -> for auto-complete feature
        elif c == KEY_TAB \
        or (c==curses.KEY_RIGHT and hinted and codePosition == codeLength):
        # or right_key when there is a suggestion
            debugFileOut = True
            # call get_hint function to return the word which fits :n-index of `code` variable
            after_appending = x + 1
            codeSplit = code.split()
            if codeSplit:
                autocomplete: str = get_hint(codeSplit[-1])
                if autocomplete and codePosition >= codeLength:
                    # autocomplete found
                    tmpLeftOfAutoComplete = get_last_substring(code,False,True)
                    tmpIndex= tmpLeftOfAutoComplete+1 if tmpLeftOfAutoComplete else 0
                    code = code[:tmpIndex] + autocomplete
                    delete_line(stdscr=stdscr, start=x, end=PREFIXlen - 1, step=-1, y=y)
                    stdscr.addstr(code)
                    codePosition = len(code)
                else:
                    # no autocomplete found
                    tmpMoveTo: int
                    if codePosition != codeLength:
                        # not at end of line
                        tmpMoveTo=codePosition+SPACElen
                        for _ in range(SPACElen+1): stdscr.delch(y, x-_)
                        code = code[:codePosition] + SPACE + code[codePosition:]
                        stdscr.addstr(code[codePosition:])
                    else:
                        # add whitespace (2 spaces)
                        code += SPACE
                        stdscr.addstr(SPACE)
                        tmpMoveTo = codeLength+SPACElen
                    # move to end of line
                    codePosition += SPACElen
                    stdscr.move(y, tmpMoveTo + PREFIXlen)
            else:
                # add whitespace (2 spaces)
                code += SPACE
                codePosition += SPACElen
                stdscr.addstr(SPACE)
                stdscr.move(y, codeLength+SPACElen + PREFIXlen)
            hinted = False

        elif c in KEY_BACKSPACE:
            debugFileOut = True

            if x > PREFIXlen-1 or y > linesStartingY:
                if hinted:
                    clear_suggestion(stdscr=stdscr, start=lastCursorX, end=width, step=1, y=y)
                    hinted = False
                stdscr.delch(y, x-1)
                if c == 330: stdscr.move(y, x - 1) # DEL key

                if x == 0:
                    y-=1 ; x=width-1
                    stdscr.move(y, x)

                if 0 < codePosition < codeLength:
                    code = code[:codePosition - 1 if codePosition - 1 > 0 else 0] + code[codePosition:]
                    codePosition-=1
                    redraw(stdscr)
                    stdscr.move(y, x-1)
                else:
                    code = code[:-1]
                    stdscr.move(y, x-1)
                    codePosition-=1
                
                hinted = display_hint(stdscr, y, PREFIXlen+codePosition-1, code, lastCursorX=0, after_appending=0, hinted=hinted, maxX=width)

                if inIndent and exitIndent(code) != None and len(tuple(deIndent(code))) > 1 and len(deIndent(code)[-2]) > len(code.split('\n')[-1]):
                    # take deindent to next line
                    currentIndent = len(code.split('\n')[-1])//SPACElen
            else:
                stdscr.move(y, x + 1)
            if code == '' and x <= PREFIXlen:
                # if no characters, clear suggestion
                clear_suggestion(stdscr=stdscr, start=PREFIXlen, end=width, step=1, y=y)

        elif c in KEY_ENTER:
            debugFileOut = True

            if code and code[-1]=='\\':
                if isWindows:
                    stdscr.move(y, 0)
                else:
                    if y+1 >= height:
                      stdscr.addstr('\n')
                    else:
                      stdscr.move(y+1, 0)
                stdscr.addstr(INDENT, curses.color_pair(2))
                lastCursorX = INDENTlen
            elif code and ((inIndent and exitIndent(code) == None) or (not inIndent and checkIfIndent(code) != None)):
                if checkIfIndent(code.split('\n'+(SPACE*currentIndent))[-1]) != None:
                    currentIndent+=1
                bash_history.append(code.split('\n')[-1])
                # ^ entering the current line into the bash history instead of the whole code ensures stability when going up and down history
                code+='\n'+(SPACE*currentIndent) ; codePosition+=1+(SPACElen*currentIndent)
                if y+1 < height:
                    if not isWindows:
                        stdscr.move(y+1, 0)
                else:
                    stdscr.move(y, 0)
                    stdscr.scroll(1)
                
                stdscr.addstr(INDENT+(SPACE*currentIndent), curses.color_pair(2))
                lastCursorX = INDENTlen
                inIndent = True
            else:
                if inIndent and code and code[-1] == '\n': code=code[:-1]
                if code:
                    # evaluate the line/block
                    if inIndent and exitIndent(code) != None and code[-1]=='\n': code+=SPACE
                    if code and (not bash_history or code != bash_history[-1]) and not inIndent:
                        bash_history.append(code)
                    history_idx = len(bash_history)
                    delete_line(stdscr=stdscr, start=width - 1, end=PREFIXlen + len(code) - 1, step=-1, y=y)

                    compiledCode, variableInformation, metaInformation = buildCode(code, variableInformation, metaInformation)
                    if compiledCode.startswith(f'# ASnake {ASnakeVersion} ERROR'):
                        ASError = True
                    else:
                        ASError = False

                    with open('ASnakeREPLCommand.lock', 'w') as f:
                        pass
                    with open('ASnakeREPLCommand.txt', 'w') as f:
                        f.write(compiledCode)
                    remove('ASnakeREPLCommand.lock')

                    if firstLine:
                        if isWindows:
                            stdscr.move(y, 0)
                        else:
                            scrollWhenYOverflow(y+1,0)
                    elif isWindows:
                        stdscr.move(y - 1, width - 1)
                    if isWindows: stdscr.nodelay(1)

                    tmpCodeYLen = (PREFIXlen + len(code)) // width
                    if not isWindows and not firstLine and tmpCodeYLen >= 1 and y+1 < height:
                        tmpIndex=(codePosition//width)+1
                        if tmpIndex < tmpCodeYLen:
                            tmp = y + (tmpCodeYLen - tmpIndex) + 1
                        else:
                            tmp=y+1
                        stdscr.move(tmp, 0) # prevents cutoff of multi-line code
                        del tmp , tmpIndex
                    del tmpCodeYLen
                    firstLine = False
                    addByte = False
                    output = ''
                    try:
                        while True:
                            # show output by character
                            if childPoll() is not None:
                                exitRoutine()
                            elif addByte:
                                output += readChildStdout(1)
                                addByte = False
                            else:
                                output = readChildStdout(1)
                            try:
                                output = output.decode()
                            except UnicodeDecodeError:
                                addByte = True
                                continue
                            if output:
                                if output == exitByte and 'ASnakeREPLCommand.txt' not in listdir():
                                    break
                                elif output == errorByte:
                                    output = ''
                                    ASError = True
                                    continue
                                elif isWindows and output == '\r':
                                    output = ''
                            else:
                                continue
                    
                            for i in range(len(output)):
                                stdscr.addstr(f"{output[i]}", curses.color_pair(3) if ASError else curses.color_pair(1))

                            stdscr.refresh()
                            if isWindows:
                                tmp = stdscr.getch()
                                if tmp == 3:
                                    raise KeyboardInterrupt
                                else:
                                    pass
                    except KeyboardInterrupt:
                        if isWindows:
                            call(['taskkill', '/PID', str(child.pid), '/F'], stderr=DEVNULL, stdout=PIPE)
                            remove('ASnakeREPLCommand.txt')
                        else:
                            kill(child.pid, stopExecution)
                        while True:
                            # need to burn rest of output
                            if addByte:
                                output += readChildStdout(1)
                                addByte = False
                            else:
                                output = readChildStdout(1)
                            try:
                                output = output.decode()
                            except UnicodeDecodeError:
                                addByte = True
                                continue
                            if not output or output == exitByte and 'ASnakeREPLCommand.txt' not in listdir():
                                break
                        stdscr.addstr('\nKeyboardInterrupt\n', curses.color_pair(3))
                        y, _ = stdscr.getyx()
                        if y + 1 < height:
                            stdscr.move(y + 1, 0) ; y += 1
                        if isWindows:
                            child = Popen(f'{pyCall} -u {runFile}', stdout=PIPE, cwd=getcwd(), shell=False)
                            firstLine = True
                    if isWindows: stdscr.nodelay(0)
                    child.stdout.flush()
                else:
                    if isWindows:
                        stdscr.move(y, 0)
                    else:
                        scrollWhenYOverflow(y+1,0)

                inIndent = False
                currentIndent = 0
                inString=False
                y, x = stdscr.getyx()
                linesStartingY = y
                stdscr.addstr(PREFIX, curses.color_pair(2))
                code = ''
                codePosition = 0
                stdscr.refresh()
        elif c == 3 and isWindows: # ctrl c
            raise KeyboardInterrupt
        elif c == 4 and not isWindows:
            if not code:
                exitRoutine()
            else:
                curses.beep()
                if x >= codeLength+PREFIXlen:
                    stdscr.delch(y, x-2)
                    stdscr.delch(y, x-2)
                else:
                    redraw(stdscr)
                    stdscr.move(y,x-2)
        elif c == CTRL_W: # ctrl w
            debugFileOut = True
            if codePosition <= 0:
                delete_line(stdscr, PREFIXlen, PREFIXlen+2, 1, y)
                stdscr.move(y, PREFIXlen)
            else:
                skipToCharacter(stdscr, x, y, delete=True)
        elif c in CTRL_LEFT:
            skipToCharacter(stdscr, x, y)
        elif c in CTRL_RIGHT:
            skipToCharacter(stdscr, x, y, direction='right')
        elif c in {575, 567}: # ctrl_up
            # don't combine with elif, we want to trap that input
            if y > linesStartingY:
                if y-1 == linesStartingY and x <= PREFIXlen:
                    stdscr.move(y - 1, PREFIXlen)
                    codePosition-=width-PREFIXlen
                elif inIndent:
                    stdscr.move(y - 1, x)
                    tmp = len(code.split('\n')[y-linesStartingY])
                    codePosition=len(''.join(code.split('\n'))[:tmp])
                else:
                    stdscr.move(y-1, x)
                    codePosition-=width
        elif c in {534, 526}: # ctrl_down
            if inIndent and (y+1-linesStartingY) <= code.count('\n'):
                stdscr.move(y + 1, x)
                codePosition+=len(code[codePosition:])
                if codePosition+INDENTlen > codeLength:
                    code+=' '*(codePosition+INDENTlen-codeLength)
                    codePosition+=(codePosition+INDENTlen-codeLength)

            elif codeLength > width:
                if codeLength // width > codePosition // width and abs((y-linesStartingY) * width + x) <= codeLength:
                    stdscr.move(y + 1, x)
                    codePosition = abs((y+1-linesStartingY) * width + x)
                    if y == linesStartingY: codePosition-=PREFIXlen
        elif c in {34,39}: # string quotes
            if codePosition == codeLength:
                code += chrC
                stdscr.addstr(chrC, curses.color_pair(5))
                if c == inString:  inString=False
                elif not inString: inString=c
            else:
                if codePosition == 0:
                    code = chrC + code[codePosition:]
                else:
                    code = code[:codePosition] + chr(c) + code[codePosition:]
                syntaxHighlightString(code[codePosition:])
                if code.count(chrC) % 2 == 0:
                      inString=False
                else: inString=c
            codePosition+=1
            stdscr.move(y,x+1)
        elif c in {-1, 410, 337}: pass
        else:
            debugFileOut = True
            if codePosition == codeLength:
                handleSyntaxHighlighting(c,lastChar=ord(code[-1]) if code else False, tmpInString=inString)
                code += chrC
                codePosition += 1
                lastCursorX = x
                if not inString:
                    if code[-1] != ' ':
                        hinted = display_hint(stdscr, y, x, code.split()[-1], lastCursorX, after_appending, hinted, width)
                    else:
                        # if a space is done on a suggestion, clear the suggestion
                        clear_suggestion(stdscr=stdscr, start=lastCursorX+1, end=width, step=1, y=y)
                if x+1 < width: stdscr.move(y, x+1)
                else: scrollWhenYOverflow(y, 0)
            else:
                if codePosition == 0:
                    code = chrC + code[codePosition:]
                else:
                    code = code[:codePosition] + chrC + code[codePosition:]
                codePosition += 1
                if len(code)+PREFIXlen < width and not inIndent: # one-line, update in-place
                    delete_line(stdscr=stdscr, start=PREFIXlen + len(code[codePosition-1:]), end=width, step=-1, y=y)
                    syntaxHighlightString(code[codePosition-1:], lastChar=ord(code[codePosition-2]), customYX=(y,x))
                else: # multi-liner, redraw entire code
                    redraw(stdscr)           

                stdscr.move(y, x+1)
                stdscr.refresh()
        
        if debug and debugFileOut:
            file_out('w', code,f"{codePosition}/{len(code)} x={x} y={y} sy={linesStartingY} bi={history_idx}",extra)


if __name__ == "__main__":
    if 'ASnakeREPLCommand.txt' in listdir():
        remove('ASnakeREPLCommand.txt')
    try:
        curses.wrapper(main)
    except (KeyboardInterrupt, BrokenPipeError):
        if 'ASnakeREPLCommand.txt' in listdir():
            try: remove('ASnakeREPLCommand.txt')
            except: pass

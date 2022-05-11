execGlobal = globals()
from os import listdir, remove
from time import sleep
while True:
    if 'ASnakeREPLCommand.txt' in listdir():
        try:
            with open('ASnakeREPLCommand.txt', 'r') as f:
                exec(f.read(), execGlobal)
        except Exception as e:
            print(chr(999998))
            print('Python ' + e.__class__.__name__ + ':\n' + str(e))
            #stdscr.addstr(error, curses.color_pair(3))
            #stdscr.move(y + error.count('\n') + 2, 0)
        remove('ASnakeREPLCommand.txt')
        print(chr(999999))
    else:
        sleep(0.01)

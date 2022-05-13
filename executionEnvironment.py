execGlobal = globals()
from os import listdir, remove
from time import sleep
while True:
    if 'ASnakeREPLCommand.txt' in listdir():
        try:
            with open('ASnakeREPLCommand.txt', 'r') as _:
                exec(_.read(), execGlobal)
        except Exception as e:
            print(chr(999998))
            print('Python ' + e.__class__.__name__ + ':\n' + str(e))
        remove('ASnakeREPLCommand.txt')
        print(chr(999999))
    else:
        sleep(0.01)

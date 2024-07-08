from os import listdir, remove
from time import sleep
from dill import dump_module, load_module
try: load_module('run.pkl')
except: pass
while True:
    if 'ASnakeREPLCommand.txt' in listdir() and 'ASnakeREPLCommand.lock' not in listdir():
        try:
            with open('ASnakeREPLCommand.txt', 'r') as _:
                try:
                    exec(_.read())
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(chr(999998),end='')
            print('Python ' + e.__class__.__name__ + ':\n' + str(e))
        finally:
            try: remove('ASnakeREPLCommand.txt')
            except: pass
            print(chr(999999))
            dump_module('run.pkl')
    else:
        try:
            sleep(0.01)
        except KeyboardInterrupt:
            exit()

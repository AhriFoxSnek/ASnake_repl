from os import listdir, remove
from time import sleep
while True:
    if 'ASnakeREPLCommand.txt' in listdir():
        try:
            with open('ASnakeREPLCommand.txt', 'r') as _:
                try:
                    exec(_.read())
                except KeyboardInterrupt:
                    try:
                        remove('ASnakeREPLCommand.txt')
                    except: raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(chr(999998),end='')
            print('Python ' + e.__class__.__name__ + ':\n' + str(e))
        finally:
            try: remove('ASnakeREPLCommand.txt')
            except: pass
            print(chr(999999))
    else:
        try:
            sleep(0.01)
        except KeyboardInterrupt:
            exit()

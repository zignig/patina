import sys, tty
def command_line():
    tty.setraw(sys.stdin)
    while True:
        char = sys.stdin.read(1)
        if ord(char) == 3: # CTRL-C
            break;
        if ord(char) == 0xd: # CTRL-C
            print()
        print(hex(ord(char)),'\r')


command_line()
import sys, tty
def command_line():
    tty.setraw(sys.stdin)
    while True:
        char = sys.stdin.read(1)
        if ord(char) == 3: # CTRL-C
            break;
        print(hex(ord(char)))


command_line()

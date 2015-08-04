from client import Client
import sys

def main(args):
    client = Client(args[0])

if __name__ == '__main__':
    main(sys.argv[1:])

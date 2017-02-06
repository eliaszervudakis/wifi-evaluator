from time import gmtime, strftime
import sys
import getopt
from scripts.analyze import analyze
from scripts.read import read
from scripts.capture import capture
from time import sleep

def print_usage_info():
    """
    Prints usage info to the console.
    """
    print('usage: run.sh [[-h] | [-d] | [-c] | [-r][-a]]')
    print('-h: Display this usage info')
    print('-d: Do all: capture, read and analyze')
    print('-c: Only capture')
    print('-r <capture_id>: Read existing capture')
    print('-a <capture_id>: Analyze existing read')

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hdcr:a:")
    except getopt.GetoptError:
        print_usage_info()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_usage_info()
            sys.exit()
        elif opt == "-d":
            capture_id = strftime("%Y.%m.%d_%H-%M-%S", gmtime())
            capture(capture_id)
            read(capture_id)
            sleep(5)
            analyze(capture_id)
        elif opt == "-c":
            capture_id = strftime("%Y.%m.%d_%H-%M-%S", gmtime())
            capture(capture_id)
        elif opt == "-r":
            capture_id = arg
            read(capture_id)
        elif opt == "-a":
            capture_id = arg
            analyze(capture_id)

if __name__ == "__main__":
    main(sys.argv[1:])
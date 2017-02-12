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
    print('-c <cap: Only capture')
    print('-r <capture_id>: Read existing capture')
    print('-a <capture_id>: Analyze existing read')

def main(argv):
    capture_id_format = "%Y.%m.%d_%H-%M-%S"
    capture_interface = "en0"
    capture_interval = 60

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
            capture_id = strftime(capture_id_format, gmtime())
            capture(capture_id,capture_interface,capture_interval)
            read(capture_id)
            sleep(20)
            analyze(capture_id,capture_interval)
        elif opt == "-c":
            capture_id = strftime(capture_id_format, gmtime())
            capture(capture_id,capture_interface,capture_interval)
        elif opt == "-r":
            capture_id = arg
            read(capture_id)
        elif opt == "-a":
            capture_id = arg
            analyze(capture_id,capture_interval)

if __name__ == "__main__":
    main(sys.argv[1:])
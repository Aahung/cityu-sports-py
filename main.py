#!/usr/bin/python
__author__ = 'Hung'

from api import API
import time
import sys
import getopt

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "u:s:t:h")
    except getopt.GetoptError:
        print 'c -s system_config -t target_config -u user_config'
        sys.exit(2)
    user_config_file = 'user_config.json'
    system_config_file = 'system_config.json'
    target_config_file = 'target_config.json'
    for opt, arg in opts:
        if opt == '-t':
            target_config_file = arg
        elif opt in ("-s"):
            system_config_file = arg
        elif opt in ("-u"):
            user_config_file = arg
        elif opt == '-h':
            print 'c -s system_config -t target_config -u user_config'
            sys.exit(1)
    api = API(open(user_config_file).read().replace('\n', ''),
              open(target_config_file).read().replace('\n', ''),
              open(system_config_file).read().replace('\n', ''))
    api.do()



if __name__ == "__main__":
    main(sys.argv[1:])
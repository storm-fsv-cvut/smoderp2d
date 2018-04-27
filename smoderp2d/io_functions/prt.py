import sys
import time
import os


def message(*arg):
    line = ''
    for i in range(len(arg)):
        line += str(arg[i]) + ' '
    # logFile.write(line+'\n')
    print line


# Prints degub message to console if constants.PARAMETER_DEBUG_PRT is True\n
#
#  if arg[0] is True, method prints arg[1:]\n
#  if arg[0] is Flase, method prints nothing
def debug_info(db, *arg):
    if not(db):
        pass
    else:
        if len(arg) > 1:
            if isinstance(arg[0], bool):
                if arg[0]:
                    line = '\t Debug: '
                    for i in range(len(arg[1:])):
                        line += str(arg[i + 1]) + ' '
                    print line
            else:
                line = '\t Debug: '
                for i in range(len(arg[0:])):
                    line += str(arg[i]) + ' '
                print line
        else:
            line = '\t Debug: '
            for i in range(len(arg[0:])):
                line += str(arg[i]) + ' '
            print line

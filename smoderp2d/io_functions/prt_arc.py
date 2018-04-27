import sys
import time
import os
import smoderp2d.constants as constants
from smoderp2d.tools.tools import get_argv

arcgis = get_argv(constants.PARAMETER_ARCGIS)
debugInfo = get_argv(constants.PARAMETER_DEBUG_PRT)
outDir = get_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)
#logFile = open(outDir+os.sep+logFileName, 'w')

#print o
#mujout = open('mujout.dat','w')
#mujout.writelines("reach.id_" + ';' + "reach.h" + ';' + "reach.V_in_from_field" + ';' + "reach.V_rest" + ';' + " reach.V_in_from_reach" + ';' + "reach.V_out"+ ';' + "reach.to_node"+'\n')


if arcgis:
    import arcpy

    def arcgis_message(*arg):
        line = ''
        for i in range(len(arg)):
            line += str(arg[i]) + ' '
        line += '\n'
        arcpy.AddMessage(line)
        # logFile.write(line)

    def arcgis_error(*arg):
        line = 'ERROR:\n'
        for i in range(len(arg)):
            line += str(arg[i]) + ' '
        line += '\n'
        arcpy.AddMessage(line)
        # logFile.write(line)
        sys.exit()

    def arcgis_info(*arg):
        line = '\t Debug:'
        for i in range(len(arg)):
            line += str(arg[i]) + ' '
        line += '\n'
        arcpy.AddMessage(line)

    def arcgis_info_pass(*arg):
        pass

    message = arcgis_message
    error = arcgis_error
    if debugInfo:
        debug = arcgis_info
    else:
        debug = arcgis_info_pass


else:
    def console_message(*arg):
        line = ''
        for i in range(len(arg)):
            line += str(arg[i]) + ' '
        # logFile.write(line+'\n')
        print line

    def console_error(*arg):
        line = 'ERROR:\n'
        for i in range(len(arg)):
            line += str(arg[i]) + ' '
        # logFile.write(line+'\n')
        print line
        sys.exit()

    # Prints degub message to console if constants.PARAMETER_DEBUG_PRT is True\n
    #
    #  if arg[0] is True, method prints arg[1:]\n
    #  if arg[0] is Flase, method prints nothing
    def console_info(*arg):
        if len(arg) > 1:
            if type(arg[0]) == bool:
                if arg[0] == True:
                    line = '\t Debug: '
                    for i in range(len(arg[1:])):
                        line += str(arg[i+1]) + ' '
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

    def console_info_pass(*arg):
        pass

    message = console_message
    error = console_error
    if debugInfo:
        debug = console_info
    else:
debug = console_info_pass

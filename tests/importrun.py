#-------------------------------------------------------------------------------
# Name:        importrun
# Purpose:     test of model after instalation
#
# Author:      jerabj11
#
# Created:     22/12/2017
# Copyright:   (c) jerabj11 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------





def main():
    import sys
    import os


    try :
      print 'importing smoderp2d ...'
      import smoderp2d.main as sm
      sys.argv = ['smod',
       'test-data\\ds_plocha',
       'test-data\\plocha.shp',
        'puda',
        'test-data\\plocha.shp',
        'LU',
        'test-data\\srazka.txt',
        '0.2',
        '60',
        'test-data\\point.shp',
        os.getcwd() + os.sep+ os.sep + 'test-out',
        'test-data\\tabulkytab_maleTau.dbf',
        'SOILVEG',
        'test-data\\toky2.shp',
        'test-data\\tab_stream_tvar.txt',
        'smoderp',
        'false']
      print 'initiating computation ...'
      sm.run()

      return 1
    except :
      print "Unexpected error:", sys.exc_info()[0]
      print "                 ", sys.exc_info()[1]
      return 0


if __name__ == '__main__':


    if (main() == 1) :
        print '\n Trial run of model has finished successfully. \n'
        raw_input('press enter ...')
    else :
        print '\n Trial run of model finished with error. \n'
        raw_input('press enter ...')

#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jerabj11
#
# Created:     22/12/2017
# Copyright:   (c) jerabj11 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------





def main():
    import sys
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
        'test-out',
        'test-data\\tabulkytab_maleTau.dbf',
        'SOILVEG',
        '#',
        '#',
        '#',
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
        raw_input('press enter ...')
    else :
        raw_input('press enter ...')

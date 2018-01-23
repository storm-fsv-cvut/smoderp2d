## @package smoderp2d.config
#  Contains the input parameters
#  
#  from sys.argv for Windows from ConfigParser in Linux


demPath = None
soilPath = None
soilAtr = None
luPath = None
luAtr = None
precipPath = None
maxDT = None
endTime = None
pointsPath = None
outDirPath = None
soilLuTabPath = None
soilLuTabAtr = None
reachPath = None
reachTabPath = None
reachTabAtr = None
arcGis  = None

mfda = None
extraOutput = None
inData = None
partialComp = None
debugPrint = None
printTimes = None
typeComp = None







# definice erroru  na urovni modulu 
# 
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class BooleanInputError(Error):
    """Exception raised for nonboolean value.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self,val):
        self.msg = 'Incorrect input parameter.' + str(type(val)) + ' with value ' + str(val) + ' assign as boolean.'
    def __str__(self):
        return repr(self.msg)
      
      


## Check for boolean varieble
#
def boolean_val(val):
  
  if isinstance(val, bool) :
    return val
  
  if isinstance(val, int) :
    """ if True == 1 then True 
        if True == 0 then False"""
    return True == val
  
  if isinstance(val, str) :
    if val.lower().strip() == 'true':
      return True
    elif val.lower().strip() == 'false':
      return False  
  
  raise BooleanInputError(val)
  
  
  
  
  


def set_config_win(arg) :
  import smoderp2d.src.constants as constants
  
  global demPath
  global soilPath
  global soilAtr
  global luPath
  global luAtr
  global precipPath
  global maxDT
  global endTime
  global pointsPath
  global outDirPath
  global soilLuTabPath
  global soilLuTabAtr
  global reachPath
  global reachTabPath
  global reachTabAtr
  global arcGis
  
  global mfda
  global extraOutput
  global inData
  global partialComp
  global debugPrint
  global printTimes
  global typeComp
  
  demPath  = sys.argv[1+constants.PARAMETER_DMT]
  soilPath = sys.argv[1+constants.PARAMETER_SOIL]
  soilAtr  = sys.argv[1+constants.PARAMETER_SOIL_TYPE]
  luPath   = sys.argv[1+constants.PARAMETER_VEGETATION]
  luAtr    = sys.argv[1+constants.PARAMETER_VEGETATION_TYPE]
  precipPath = sys.argv[1+constants.PARAMETER_PATH_TO_RAINFALL_FILE]
  maxDT      = sys.argv[1+constants.PARAMETER_MAX_DELTA_T]
  endTime    = sys.argv[1+constants.PARAMETER_END_TIME]
  pointsPath     = sys.argv[1+constants.PARAMETER_POINTS]
  outDirPath     = sys.argv[1+constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY]
  soilLuTabPath  = sys.argv[1+constants.PARAMETER_SOILVEGTABLE]
  soilLuTabAtr   = sys.argv[1+constants.PARAMETER_SOILVEGTABLE_CODE]
  reachPath      = sys.argv[1+constants.PARAMETER_STREAM]
  reachTabPath   = sys.argv[1+constants.PARAMETER_STREAMTABLE]
  reachTabAtr    = sys.argv[1+constants.PARAMETER_STREAMTABLE_CODE]
  arcGis         = sys.argv[1+constants.PARAMETER_ARCGIS]


  mfda        = sys.argv[1+constants.PARAMETER_MFDA]
  extraOutput = sys.argv[1+constants.PARAMETER_EXTRA_OUTPUT]
  inData      = sys.argv[1+constants.PARAMETER_INDATA]
  partialComp = sys.argv[1+constants.PARAMETER_PARTIAL_COMPUTING]
  debugPrint  = sys.argv[1+constants.PARAMETER_DEBUG_PRT]
  printTimes  = sys.argv[1+constants.PARAMETER_PRINT_TIME]
  typeComp    = sys.argv[1+constants.PARAMETER_TYPE_COMPUTING]
  
  
  arcGis      = boolean_val(arcGis)
  mfda        = boolean_val(mfda)
  extraOutput = boolean_val(extraOutput)
  
  
  
def set_config_lin(args) :
  import ConfigParser
  
  global demPath
  global soilPath
  global soilAtr
  global luPath
  global luAtr
  global precipPath
  global maxDT
  global endTime
  global pointsPath
  global outDirPath
  global soilLuTabPath
  global soilLuTabAtr
  global reachPath
  global reachTabPath
  global reachTabAtr
  global arcGis
  
  global mfda
  global extraOutput
  global inData
  global partialComp
  global debugPrint
  global printTimes
  global typeComp
  
  Config = ConfigParser.ConfigParser()
  Config.read(args.indata)


  demPath    = Config.get('GIS','dem')
  soilPath   = Config.get('GIS','soil')
  soilAtr    = Config.get('shape atr','soil-atr')
  luPath     = Config.get('GIS','lu')
  luAtr      = Config.get('shape atr','lu-atr')
  precipPath = Config.get('srazka','file')
  maxDT      = Config.get('time','maxdt')
  endTime    = Config.get('time','endtime')
  pointsPath = Config.get('Other','points')
  outDirPath = Config.get('Other','outdir')
  soilLuTabPath = Config.get('Other','soilvegtab')
  soilLuTabAtr  = Config.get('Other','soilvegcode')
  reachPath     = Config.get('Other','streamshp')
  reachTabPath  = Config.get('Other','streamtab')
  reachTabAtr   = Config.get('Other','streamtabcode')
  arcGis        = Config.get('Other','arcgis')


  mfda        = Config.get('Other','mfda')
  extraOutput = Config.get('Other','extraout')
  inData      = Config.get('Other','indata')
  partialComp = Config.get('Other','partialcomp')
  debugPrint  = Config.get('Other','debugprt')
  printTimes  = Config.get('Other','printtimes')
  typeComp    = Config.get('Other','typecomp')

  # uprava data typu
  arcGis      = boolean_val(arcGis)
  mfda        = boolean_val(mfda)
  extraOutput = boolean_val(extraOutput)
  
  
  
  if partialComp == 'roff' :
    try:
      endTime = float(endTime) * 60
    except ValueError:
      print 'End time taken from indata.save file...'
  else:
    endTime = float(endTime) * 60
  
  
  if partialComp == 'roff' :
    try:
      maxDT   = float(maxDT)
    except ValueError:
      print 'Max time step from indata.save file...'
  else:
    maxDT   = float(maxDT)


# nektede jsou dodatecne zmenit pri roff vypoctu
# coz je volano v smoderp2d.setting
def set_outDirPath(val) :
  global outDirPath
  outDirPath = val

# nektede jsou dodatecne zmenit pri roff vypoctu
# coz je volano v smoderp2d.setting
def set_endTime(val) :
  global endTime
  endTime = val

# nektede jsou dodatecne zmenit pri roff vypoctu
# coz je volano v smoderp2d.setting  
def set_mfda(val) :
  global mfda
  mfda = val


# nektede jsou dodatecne zmenit pri roff vypoctu
# coz je volano v smoderp2d.setting  
def set_outDirPath(val) :
  outDirPath = val
  
# nektede jsou dodatecne zmenit pri roff vypoctu
# coz je volano v smoderp2d.setting  
def set_outDirPath(val) :
  outDirPath = val

# nektede jsou dodatecne zmenit pri roff vypoctu
# coz je volano v smoderp2d.setting  
def set_outDirPath(val) :
  outDirPath = val
  
  
  
  
  
  
  
  
  


def get_demPath():
  return demPath

def get_soilPath():
  return soilPath

def get_soilAtr():
  return soilAtr

def get_luPath():
  return luPath

def get_luAtr():
  return luAtr

def get_precipPath():
  return precipPath

def get_maxDT():
  return maxDT

def get_endTime():
  return endTime

def get_pointsPath():
  return pointsPath

def get_outDirPath():
  return outDirPath

def get_soilLuTabPath():
  return soilLuTabPath

def get_soilLuTabAtr():
  return soilLuTabAtr

def get_reachPath():
  return reachPath

def get_reachTabPath():
  return reachTabPath

def get_reachTabAtr():
  return reachTabAtr

def get_arcGis():
  return arcGis


def get_mfda():
  return mfda

def get_extraOutput():
  return extraOutput

def get_inData():
  return inData

def get_partialComp():
  return partialComp

def get_debugPrint():
  return debugPrint

def get_printTimes():
  return printTimes

def get_typeComp():
  return typeComp

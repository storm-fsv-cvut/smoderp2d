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




def set_config_win(arg) :
  import smoderp2d.src.constants as constants
  
  global demPath
  global soilPath
  global soilAtr
  global luPath
  global luAtr
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
  
  
  
def set_config_lin(arg) :
  import smoderp2d.src.constants as constants
  
  global demPath
  global soilPath
  global soilAtr
  global luPath
  global luAtr
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


  demPath   = Config.get('GIS','dem'))
  soilPath  = Config.get('GIS','soil'))
  soilAtr   = Config.get('shape atr','soil-atr'))
  luPath    = Config.get('GIS','lu'))
  luAtr     = Config.get('shape atr','lu-atr'))
   = Config.get('srazka','file'))
   = Config.get('time','maxdt'))
   = Config.get('time','endtime'))
   = Config.get('Other','points'))
   = Config.get('Other','outdir'))
   = Config.get('Other','soilvegtab'))
   = Config.get('Other','soilvegcode'))
   = Config.get('Other','streamshp'))
   = Config.get('Other','streamtab'))
   = Config.get('Other','streamtabcode'))
   = Config.get('Other','arcgis'))


   = Config.get('Other','mfda'))
   = Config.get('Other','extraout'))
   = Config.get('Other','indata'))
   = Config.get('Other','partialcomp'))
   = Config.get('Other','debugprt'))
   = Config.get('Other','printtimes'))
   = Config.get('Other','typecomp'))














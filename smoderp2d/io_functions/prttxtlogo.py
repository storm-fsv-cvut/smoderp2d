# small script to print a smoderp2d logo
#  before data initiation


with open('smoderp2d/io_functions/txtlogo.txt', 'r') as f:
    d = f.readlines()

try:
    import arcpy
    for line in d:
        arcpy.AddMessage(line.replace('\n', ''))
except ImportError:
    for line in d:
        print line.replace('\n', '')

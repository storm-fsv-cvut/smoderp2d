import pickle
import sys
import numpy

with open(sys.argv[1], 'rb') as f:
  data = pickle.load(f)

for item in data:
  if type(item) == numpy.ndarray:
    print type(item)
  else:
    print item






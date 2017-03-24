import math

def shallowSurfaceKinematic(sur):
  
  a = sur.a
  b = sur.b
  h = sur.h
  
  return math.pow(h,b) * a
  
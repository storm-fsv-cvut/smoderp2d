import math






##def update_b(h,old_b,rillRatio,l):
  ##curr_V = h*(h/rillRatio)
  ##old__V = old_b*old_b*rillRatio
  ##if curr_V > old__V:
    ##b = math.sqrt(curr_V/(rillRatio*l))
    ##y = rillRatio*b
    ##h = y
  ##else:
    ##b = old__b
    ##h = h

  ##return h, b


def update_hb(V_to_rill,V_rill_pre,rillRatio,l,b,ratio):
  V = V_to_rill/ratio + V_rill_pre
  newb = math.sqrt(V/(rillRatio*l))
  if newb > b :
    b = newb
    h = V/(b*l)
  else:
    h = V/(b*l)
  return h, b

def rill(V_to_rill,V_rill_rest,rillRatio,l,b,delta_t,ratio,n,slope,pixelArea):
  print 'rill'
  V_rill_runoff = 0
  delta_t = delta_t / ratio
  v = [0] * ratio
  q = [0] * ratio
  for k in range( ratio ):
    h, b = update_hb(V_to_rill,V_rill_rest,rillRatio,l,b,ratio)
    R_rill = (h*b)/(b + 2*h)
    v[k] = math.pow(R_rill,(2.0/3.0)) * 1/n * math.pow(slope/100,0.5) # m/s
    q[k] = v[k] * rillRatio * b * b # [m3/s]
    V = q[k]*delta_t
    courant = (v[k]*delta_t)/math.sqrt(pixelArea)
    if courant<0.6 :
      return b, V_rill_runoff, V_rill_rest, q, v, courant
    if V>V_to_rill/ratio + V_rill_rest:
      V_rill_rest = 0.0
      V_rill_runoff += V_to_rill/ratio+V_rill_rest
    else:
      V_rill_rest = V_to_rill/ratio - V + V_rill_rest
      V_rill_runoff += V
  
  return b, V_rill_runoff, V_rill_rest, q, v, courant
  

def rillCalculations(h_rill, V_rill_rest, b, pixelArea, l, rillRatio, n, slope, delta_t, ratio):

  V_to_rill = h_rill*pixelArea
  V_rill_rest_tmp = V_rill_rest
  b_tmp = b
  delta_t_tmp = delta_t
  courant = 1.0


  while (courant > 0.5) :
    V_rill_rest = V_rill_rest_tmp
    b = b_tmp
    delta_t = delta_t_tmp
    b, V_rill_runoff, V_rill_rest, q, v, courant = rill(V_to_rill,V_rill_rest,rillRatio,l,b,delta_t,ratio,n,slope,pixelArea)
    print courant
    print ratio
    if (courant > 0.5):
      ratio += 1
  





  qMax = max(q)
  vMax = max(v)

  return b, V_rill_runoff, V_rill_rest, qMax, vMax, ratio

b, V_rill_runoff, V_rill_rest, qMax, vMax, ratio = rillCalculations(h_rill=0.1, V_rill_rest=0.0, b=0.0, pixelArea=5, l=5, rillRatio=0.7, n=0.035, slope=2.001, delta_t=10.2, ratio=1)
print b
print 
b, V_rill_runoff, V_rill_rest, qMax, vMax, ratio = rillCalculations(h_rill=0.1, V_rill_rest=0.0, b=b, pixelArea=5, l=5, rillRatio=0.7, n=0.035, slope=2.001, delta_t=10.2, ratio=ratio)
print b



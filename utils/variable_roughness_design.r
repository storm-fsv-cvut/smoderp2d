# variants to incorporate variable roughness 


# water level
h_m = seq(0,0.01,by=0.0001) 

# minimal Mannings roughness
nmin =  0.03
# maximal Mannings roughness
nmax = nmin * 10
# mannings parameters
y = 5/3
b = 0.5
# slope
slope = 0.01

# pawer-law with a calculation
q0 <- function(h,n,slope,y,b) {
  return (1/n*slope**y*h**b)
}

# pawer-law without a calculation
q <- function(h,aa,b) {
  return (aa*h**b)
}

# variable roughness
n <- function(nmax, nmin, h) 
{
  cutoff = 0.005
  out = c()
  
  a = (nmin-nmax)/cutoff
  b = nmax
  for (ih in h){
    if (ih>cutoff) out = c(out, nmin)
    if (ih<=cutoff) out = c(out, a*ih+b)
  }
  
  return(out)
}

# calculated aa
aa_f <- function(aa, h) 
{
  cutoff = 0.005
  out = c()
  
  aa_min = aa/10
  aa_max = aa
  print (aa_max)
  
  for (ih in h){
    if (ih>cutoff) out = c(out, aa_max)
    if (ih<=cutoff) out = c(out, aa_min + (0.001)*1/exp(-ih*500))
  }
  
  return(out)
}

# smooth  variable roughness
nsmooth <- function(nmax, nmin, h)
{
  cutoff = 0.005
  out = c()

  a = 1/(nmax-nmin)

  for (ih in h){
      out = c(out, nmin + (nmax-nmin)*exp(-a*ih*1/cutoff))
  }

  return(out)
}


aa = 1/nmin*slope**y
aa_min = 1/nmin*slope**y/10



layout(matrix(c(1,2,3), ncol = 3))
plot(h_m, n(nmax, nmin, h_m), xlab = 'w level metr', ylab = 'n', col = 2, type = 'l')
# abline(h = nmax)
# abline(h = nmin)


plot(h_m, 1/n(nmax, nmin, h_m)*slope**y, xlab = 'w level metr', ylab = 'aa', col = 2, type = 'l')
plot(h_m, aa_f(aa, h_m), xlab = 'w level metr', ylab = 'aa', col = 2, type = 'l')


layout(matrix(c(1,2), ncol = 2))
plot(h_m, nsmooth(nmax, nmin, h_m), xlab = 'w level metr', ylab = 'n', col = 2, type = 'l')
abline(h = nmax, lty = 2)
abline(h = nmin, lty = 2)
plot(h_m, 1/nsmooth(nmax, nmin, h_m)*slope**y, xlab = 'w level metr', ylab = 'aa', col = 2, type = 'l')


layout(matrix(c(1,2,3), ncol = 3))
plot(h_m, q0(n = n(nmax, nmin, h_m), slope = slope, y = y, b = b, h = h_m
             ), ylab = 'discharge (changing n)', xlab = 'w level metr', type = 'l')
plot(h_m, q0(n = nsmooth(nmax, nmin, h_m), slope = slope, y = y, b = b, h = h_m
             ), ylab = 'discharge (smoothly changing n)', xlab = 'w level metr', type = 'l')
plot(h_m, q(h_m, aa, b), ylab = 'discharge (original)', xlab = 'w level metr', type = 'l')

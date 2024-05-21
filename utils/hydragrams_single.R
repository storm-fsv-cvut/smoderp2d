##############################################
# Script quickly plots SMODERP2D model results 
##############################################
#
#
# Setting
# In setting set the location of your data
#
library('manipulate')
# install package is missing with: install.packages("manipulate")
#
# root dir
root  <-  "d:/0_Smoderp/00_QGtest_ds_plocha/out2"
root  <-  "d:/0_Smoderp/02_AGPro_provider/out19_AG"

root  <-  "tests/data/output/"
root  <-  "H:/2_granty_projekty/2_Bezici/2022_RAGO/01_reseni_projektu/02_SmoderpSimulace/Svodnice_velvary/_out/N100_B_IC2_ZBGD"
root  <-  "H:/2_granty_projekty/2_Bezici/2022_RAGO/01_reseni_projektu/02_SmoderpSimulace/Svodnice_velvary/_out/compare"


root  <-  "jj-tests/"
#root  <-  "d:/2_granty_projekty/2_Bezici/2022_RAGO/01_reseni_projektu/00_test_Smoderp/out2"

# output dir
outdir <- c('diffusionsheet/control_point/', 'kinematicsheet/control_point/')
# choose points to be printed (*.dat file v output dir)
# point000.dat -> id = 1
# point001.dat -> id = 2
# atd...
id1_ = 6
id2_ = 7
id1_ = 5
id2_ = id1_+6
#2+6;1+4
# End setting  
#
#


#
# Do no edit rest of the scipt!
#
#
#
# Functions
#
nactibod = function(dir_,sep_  = ';', skip_ = 3, extension_ = '*.dat')
{
  files = list.files(dir_,pattern = '*.dat')
  pixel = read.table(paste(dir_,'/',files[1],sep = ''),skip=2,nrows = 1,comment.char = '')
  pixel = as.numeric(pixel[2])
  H = list()
  for (file_ in files) {
    name_ = substr(file_,1,8)
    H[[name_]] = read.table(paste(dir_,'/',file_,sep = ''),sep = sep_,header = TRUE,skip=skip_,comment.char = '')
  }
  return(H)
}

pp = function(t1,t2,sel,add_,sel2,od,do,stejny,titles)
  {
  dd1 = which(od < t1[,1] & t1[,1] < do)
  dd2 = which(od < t2[,1] & t2[,1] < do)
  if (stejny) {
    r1 = range(t1[[sel]][dd1],t2[[sel2]][dd2],na.rm = TRUE)
    r1 = range(t1[[sel]],t2[[sel2]],na.rm = TRUE)
    r2 = r1
  } else {
    r1 = range(t1[[sel]][dd1],na.rm = TRUE)
    r1 = range(t1[[sel]],na.rm = TRUE)
    r2 = range(t2[[sel2]][dd2],na.rm = TRUE)
    r2 = range(t2[[sel2]],na.rm = TRUE)
  }
  names1_ = names(t1)
  names2_ = names(t2)
  par(mar=c(4,4,4,4))
  plot(t1[,1],t1[[sel]],
       ylab = '',type = 'o',lwd=2,xlim = c(od,do),ylim=r1,cex=0.5)
  grid()
  mtext(paste(basename(titles[1]),":",sel),side = 3,line = 0.8,adj = 0,cex = 1.5)
  mtext(names1_[sel],side = 2,line = 3)
  if (add_) {
    par(new=TRUE)
    plot(t2[,1],t2[[sel2]],
         axes = FALSE, ylab = '',type = 'o',col=2,lwd=2,xlim = c(od,do),ylim=r2,cex=0.5)
    axis(4,col.ticks = 2, col = 2,col.axis=2)
    mtext(paste(basename(titles[2]),":",sel2),side = 3,line = 2,adj = 1,cex = 1.5, col=2)
    mtext(names2_[sel2],side = 4,line = 3,col = 2)
  }
}

plot_ = function(id1,id2,title='')
  {
  t1 = H[[id1]]
  t2 = H[[id2]]
  titles = names(H)[c(id1,id2)]
  names1_ = names(H[[id1]])
  names2_ = names(H[[id2]])
  # t1$X..time.s. = t1$time.s.
  n1 = length(t1[1,])
  m = length(t1[,1])
  maxCas = t1[,1][m]
  n2 = length(t2[1,])
  manipulate(pp(t1,t2,sel,add_,sel2,od,do,stejny,titles),
             # sel = slider(initial = 5,1,n1,label = 'spoupec v levem grafu'),
             sel = picker(as.list(names1_)),
             add_= checkbox(TRUE,'pridat druhy graf'),
             stejny= checkbox(FALSE,'stejny meritka'),
             # sel2 = slider(initial = n2, 1,n2,label = 'spoupec v pravem grafu'),
             sel2 = picker(as.list(names2_)),
             od = slider(initial = 0     ,0,maxCas,label = 'cas od'),
             do = slider(initial = maxCas,0,maxCas,label = 'cas do')
             )
}
#
# End Functions 
#
#

#
#
# Main
#
dir_ = paste(root, outdir, sep='/')
sep_  = ';'
skip_ = 0
extension_ = '*.csv'

files  = c()
for (idir_ in dir_) {
  files = c(files,list.files(idir_,pattern = '*.csv',full.names = TRUE))
}

pixel = read.table(paste(files[1],sep = ''),skip=1,nrows = 1,comment.char = '')
pixel = as.numeric(pixel[7])
H = list()
for (file_ in files) {
  
  print (file_)
  name_ = substr(file_,1,8)
  name_ = file_
  skip_ = 1
  d = read.table(file_, sep = sep_, header = TRUE, skip=skip_, comment.char = '#')
  # print (grepl('infiltration.m.', x = names(d)))
  if (any(grepl('infiltration.m.', x = names(d)))){
    
    d$cumRainfall_m3 = cumsum(d$rainfall.m.*pixel)
    d$cumInfiltration_m3 = cumsum(d$infiltration.m.*pixel)
    d$cumSheetRunoff_m3 = cumsum(d$sheetVRunoff.m3.)
    # d$cumRillRunoff_m3 = cumsum(d$)
    # d$cumInflows_m3 = cumsum(d$vInflow.m3.)
    # d$cumSurfaceRunoff_m3 = cumsum(d$surfa)
  }
  H[[name_]] = d
}

plot_(id1_,id2_)


### vse nastavujes v hlavicce ###
# cesta k funkci, snad snad do smoderp/ snad automaticky
path = dirname(parent.frame(2)$ofile)
if(length(path) != 0){setwd(path);setwd('..')}
dir_ = "out/"
library(fields)


# convert -delay 100 -loop 0 *.png animation.gif



# files = list.files(dir_,pattern = '*.dat')
# sep_  = ';'
# skip_ = 3
# H = read.table(paste(dir_,'/',files[1],sep = ''),sep = sep_,header = TRUE,skip=skip_,comment.char = '')
# 
# 
# 
# 
dir_ = paste(dir_,'prubeh/',sep='')
files = list.files(dir_,pattern = '*.asc')
n = length(files)
D = c()
rr = c()
jjj = c()
for (i in 1:n){
  rr = range(rr,values(raster(paste(dir_,files[i],sep=''))),na.rm = TRUE)
  D = c(D,raster(paste(dir_,files[i],sep='')))
  # plot(D,main=files[i])
  
  jjj = c(jjj,files[i])
  print (paste(i,files[i]))
}

# manipulate({
#   layout(matrix(c(1,2,2),ncol=1))
#   plot(H$X..Time.s.,H$Rainfall.m.)
#   abline(v=H$X..Time.s.[i])
#   plot(D[[i]])
#   },i=slider(1,length(D)))






setwd("~/Documents/Smoderp/curr/out/prubeh/")
n = length(D)


for (i in 1:n){
  jmeno = paste(sprintf('%08d',i),'.png',sep='')
  # png(jmeno)
  # layout(matrix(c(1,2,2),ncol=1))
  par(mar=c(4,4,4,5))
  # plot(H$X..Time.s.,H$Rainfall.m.,type='h')
  # abline(v=H$X..Time.s.[i])
  # image(D[[i]])
  plot(D[[i]],main=jjj[i])
  mtext('X [m]',side = 1,line = 2)
  mtext('Y [m]',side = 2,line = 2)
  # imageScale(D[[i]])
  # mtext(jjj[i],side=3,line=3,cex = 2.0)
  grid()
  # image.plot(D[[1]], legend.only = TRUE, breaks = 6, col = 5)
  # dev.off()
}


### vse nastavujes v hlavicce ###
# cesta k funkci, snad snad do smoderp/ snad automaticky
path = dirname(parent.frame(2)$ofile)
if(length(path) != 0){setwd(path);setwd('..')}
source('rscripty/hydragramy_fnc.R')



# cesta k datum
dir_ = 'out'
jpegven =  'out.jpeg'
#
#
#
#
subset = c(2,11,6,20,15,18,21,19)
# subset = c(10,19)
oddo   = 1:223
#
#
#

# takhle to funguje jako predtim dva grafy z jednoho bodu
# id1_ = 1
# id2_ = 1
sep_  = ';'
skip_ = 3
extension_ = '*.dat'
#################################


files = list.files(dir_,pattern = '*.dat')
pixel = read.table(paste(dir_,'/',files[1],sep = ''),skip=2,nrows = 1,comment.char = '')
pixel = as.numeric(pixel[2])
H = list()




for (file_ in files) {
  # print (file_)
  name_ = substr(file_,1,8)
  dd = read.table(paste(dir_,'/',file_,sep = ''),sep = sep_,header = TRUE,skip=skip_,comment.char = '')
  if (length(dd$X..Time.s.)>0){
    H[[name_]] = dd
  }
}

n = length(H)
names_ = names(H[[1]])


oddo   = 1:length(H[[1]]$X..Time.s.)

print('ktere:')
print(names_[subset])
print('od do [s]:')
print(range(H[[1]]$X..Time.s.[oddo]))
m = length(subset)
names_ = names(H[[1]][subset])

yrange = matrix(NA,ncol=2,nrow=m)
for (i in names(H)){
  ii = 1
  for (j in names_){
    # print (j,range(H[[i]][[j]]))
    # print (j,range(H[[i]][[j]]))
    yrange[ii,] = range(c(yrange[ii,],H[[i]][[j]][oddo]),na.rm = TRUE)
    ii = ii + 1
  }
}

jpeg(jpegven,width = 300*m, height = 300*n,pointsize = 15)
layout(matrix(1:(m*n),ncol = m,nrow=n,byrow = TRUE))
for (i in names(H)){
  ii=1
  for (j in names_){
    plot(H[[i]]$X..Time.s.[oddo],H[[i]][[j]][oddo],main=paste(i,j),type='l',ylim=yrange[ii,])
    ii = ii + 1
  }
}
dev.off()  





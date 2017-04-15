### vse nastavujes v hlavicce ###
# cesta k funkci, snad snad do smoderp/ snad automaticky
path = dirname(parent.frame(2)$ofile)
if(length(path) != 0){setwd(path);setwd('..')}
source('rscripty/hydragramy_vsechny_fce.R')


# cesta k datum
dir_ = 'out/'


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
  print (file_)
  name_ = substr(file_,1,8)
  dd = read.table(paste(dir_,'/',file_,sep = ''),sep = sep_,header = TRUE,skip=skip_,comment.char = '')
  if (length(dd$X..Time.s.)>0){
    H[[name_]] = dd
  }
}

plot_(H)

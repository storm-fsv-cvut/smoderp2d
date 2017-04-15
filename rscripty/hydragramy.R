### vse nastavujes v hlavicce ###
# cesta k funkci, snad snad do smoderp/ snad automaticky
path = dirname(parent.frame(2)$ofile)
if(length(path) != 0){setwd(path);setwd('..')}
source('rscripty/hydragramy_fnc.R')

# cesta k datum, vypln
dir_ = 'out'
# 

# takhle muzes porovnat dva body
id1_ = 1
id2_ = 1



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
  H[[name_]] = read.table(paste(dir_,'/',file_,sep = ''),sep = sep_,header = TRUE,skip=skip_,comment.char = '')
}

plot_(id1_,id2_)



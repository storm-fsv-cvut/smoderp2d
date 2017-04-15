rm(list=ls())
library(manipulate)
setwd("~/Documents/Smoderp/curr/rscripty")
#
##### H   je global 
#
plot_ = function(bod){
  jmeno = paste('bod',bod,sep='_')
  print(jmeno)
  df = H[[jmeno]]
  par(mar=c(4,4,4,4))
  plot(df$Time_s,df$Water_level_m,xlab = 'Time',ylab = 'Water table [m]',axes = TRUE,type = 'l',main = jmeno)
  par(new=TRUE)
  plot(df$Time_s,df$Flow_m3_s,ylab ='',xlab = '',axes = FALSE)
  axis(4)
  mtext(text = 'Flow m3/s',side = 4,line = 3)
  
}


h = read.table('../jjout/points_hydrographs_sub.txt',skip = 7,header = TRUE)
n = length(h[1,])/4

poradi = c()
jednatabluka=  seq(1,n*4,by=4)
for (i in jednatabluka+1){
  poradi = c(poradi, h[1,i])
}
  Z
  

jt = jednatabluka
H = list()
Jmena = c()
for (i in poradi){
  jmeno = paste('bod',i,sep='_')
  H[[jmeno]] = as.data.frame(h[,c(jt[i],jt[i]+2,jt[i]+3)])
  colnames(H[[jmeno]]) <- c("Time_s", "Water_level_m", "Flow_m3_s")
}

manipulate(plot_(b),b=slider(1,n))




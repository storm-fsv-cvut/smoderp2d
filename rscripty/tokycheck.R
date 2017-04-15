# setwd("~/Documents/Smoderp/curr/")
# wd = read.table('mujout.dat',sep=';',header = TRUE)
# 
# d = c()
# n = length(wd$reach.id_)
# m = unique(wd$reach.id_) + 1
# for (i in 1:n){
#   ln = paste('V',wd[i,1],sep='')
#   d[[ln]] = rbind(d[[ln]],wd[i,])
# }
# 
# 
# # pdf("plot%03d.pdf")
# par(mar=c(1,3,2,1))
# layout(matrix(c(1:(length(m)-1)),ncol=1))
# for (j in m){
#   wd = d[[j]]
#   jmena = names(wd)
#   for (k in 2:(length(jmena)-1)){
#     plot(wd[,k],ylab = '')
#     if (k == 6){
#       mtext(paste('usek',wd[1,1],jmena[k],'to node',wd$reach.to_node[1]),side = 3,line = 0)
#     }else{
#       mtext(paste('usek',wd[1,1],jmena[k]),side = 3,line = 0)
#     }
#   }
# }
# # dev.off()

# plot(d[[1]]$reach.V_out,main=paste('usek', d[[1]]$reach.id_[1], 'do', d[[1]]$reach.to_node[1]))
# do = d[[1]]$reach.to_node[1]+1
# plot(d[[do]]$reach.V_in_from_reach,main=paste('usek',d[[do]]$reach.id_[1],'z useku', d[[1]]$reach.id_[1]))



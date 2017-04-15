library('manipulate')

pp = function(t1,t2,sel,add_,sel2,od,do,stejny,titles)
  {
  dd = which(od < t1$X..Time & t1$X..Time < do)
  if (stejny) {
    r1 = range(t1[[sel]][dd],t2[[sel2]][dd],na.rm = TRUE)
    r1 = range(t1[[sel]],t2[[sel2]],na.rm = TRUE)
    r2 = r1
  } else {
    r1 = range(t1[[sel]][dd],na.rm = TRUE)
    r1 = range(t1[[sel]],na.rm = TRUE)
    r2 = range(t2[[sel2]][dd],na.rm = TRUE)
    r2 = range(t2[[sel2]],na.rm = TRUE)
  }
  # print (c(r1,r2))
  names1_ = names(t1)
  names2_ = names(t2)
  par(mar=c(4,4,4,4))
  plot(t1$X..Time,t1[[sel]],
       ylab = '',type = 'o',lwd=2,xlim = c(od,do),ylim=r1,cex=0.5)
  grid()
  mtext(paste(titles[1],":",sel),side = 3,line = 1,adj = 0,cex = 1.5)
  mtext(names1_[sel],side = 2,line = 3)
  if (add_) {
    par(new=TRUE)
    plot(t1$X..Time,t2[[sel2]],
         axes = FALSE, ylab = '',type = 'o',col=2,lwd=2,xlim = c(od,do),ylim=r2,cex=0.5)
    axis(4,col.ticks = 2, col = 2,col.axis=2)
    mtext(paste(titles[2],":",sel2),side = 3,line = 1,adj = 1,cex = 1.5, col=2)
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
  # i=1
  # print ("")
  # print('graf nalevo:')
  # for (n in names1_ ){
  #   print(paste(i,'...',n))
  #   i = i + 1 
  # }
  # i=1
  # print ("")
  # print('graf napravo:')
  # for (n in names2_ ){
  #   print(paste(i,'...',n))
  #   i = i + 1 
  # }
  t1$X..Time.s. = t1$X..Time.s./60
  n1 = length(t1[1,])
  m = length(t1[,1])
  maxCas = t1$X..Time[m]
  n2 = length(t2[1,])

  manipulate(pp(t1,t2,sel,add_,sel2,od,do,stejny,titles),
             # sel = slider(initial = 5,1,n1,label = 'spoupec v levem grafu'),
             sel = picker(as.list(names1_)),#initial = 'Surface_Flow.m3.s.'),
             add_= checkbox(TRUE,'pridat druhy graf'),
             stejny= checkbox(FALSE,'stejny meritka'),
             # sel2 = slider(initial = n2, 1,n2,label = 'spoupec v pravem grafu'),
             sel2 = picker(as.list(names2_)),#initial = 'ratio'),
             od = slider(initial = 0     ,0,maxCas,label = 'cas od'),
             do = slider(initial = maxCas,1,maxCas,label = 'cas do')
             )
  
  
}

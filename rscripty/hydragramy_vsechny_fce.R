library('manipulate')


pp = function(D,co_,od,do){
  n = length(D)
  jmena  = names(D)
  jmena_ = names(D[[1]])
  rr = c()
  
  for (i in (1:n)){
    rr = range(rr,range(D[[i]][[co_]][od:do]))
  }
  
  plot(NA,xlim=range(D[[1]][od:do,1]/60),ylim=rr,xlab='cas',ylab=names(D[[1]][co_]))
  
  for (i in (1:n)){
    lines(D[[i]][od:do,1]/60,D[[i]][[co_]][od:do],col=i)
  }
  
  par(mar=c(4,4,3,10))
  par(xpd=TRUE)
  legend(max(D[[i]][od:do,1]/60 + 0.01*(D[[i]][od:do,1]/60)),min(rr),legend = jmena,col=(1:n),lty = 1,yjust = 0)
  par(xpd=FALSE)
}


plot_ = function(D)
{
  names1_ = names(D[[1]])
  manipulate(pp(D,co_,od,do),
             co_ = picker(as.list(names1_),initial = 'Surface_Flow.m3.s.'),
             od  = slider(min = 1,max = length(D[[1]]$X..Time.s.),initial = 1),
             do  = slider(min = 1,max = length(D[[1]]$X..Time.s.),initial = length(D[[1]]$X..Time.s.))
  )
}
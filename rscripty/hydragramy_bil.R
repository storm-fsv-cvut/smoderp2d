BIL = function(id_,pixel){
  n = length(H[[id_]][[1]])
  if (length(H[[id_]]) == 11){
    in_ = sum(H[[id_]]$Rainfall.m.)*pixel + sum(H[[id_]]$V_inflow.m3.)
    out_= sum(H[[id_]]$Infiltration.m.)*pixel + sum(H[[id_]]$V_runoff.m3.)
    rest = H[[id_]]$V_rest.m3.[n] - sum(H[[id_]]$Surface_retetion.m.)*pixel
    print (paste('point', id_-1, 'bilance',in_-out_-rest))
  } else if (length(H[[id_]]) == 16) {
    in_ = sum(H[[id_]]$Rainfall.m.)*pixel + sum(H[[id_]]$V_inflow.m3.)
    out_= sum(H[[id_]]$Infiltration.m.)*pixel + sum(H[[id_]]$V_runoff.m3.) + sum(H[[id_]]$Rill_V_runoff.m3.)
    rest = H[[id_]]$V_rest.m3.[n] + H[[id_]]$Rill_V_rest[n]
    print (paste('point', id_-1, 'bilance',in_-out_-rest))
  }
}



BIL(id1_,pixel)
BIL(id2_,pixel)



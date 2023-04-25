# @package smoderp2d.time_step methods to performe
#  time step, and to store intermeriate variables

import math
from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infiltration



import copy
import numpy as np
import numpy.ma as ma
import scipy as sp

# from smoderp2d.core.surface import runoff
# from smoderp2d.core.surface import surface_retention

from smoderp2d.core.general import Globals, GridGlobals

# from smoerp2d.core.surface import sheet_runoff
from smoderp2d.core.surface import sheet_runoff

infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.000  # [m]


# Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStepImplicit:
    
    # objective function  
    def model(self,
                h_new,
              dt,
              h_old,
              list_fd,
              r,c,
              a,b,
              act_rain,
              soil_type,
              pixel_area):

        #calculating sheet runoff from all cells
        sheet_flow = np.zeros((r*c))
        # print(a)
        # print(b)
        # input()
       
        sheet_flow =ma.filled(sheet_runoff(a,b,ma.array(h_new.reshape(r,c))),fill_value=0.0).ravel()/pixel_area # [m/s] 
        

        sheet_flow = np.nan_to_num(sheet_flow,posinf=0,neginf=0)
        # setting all residuals to zero
        res = np.zeros((r*c))

        # Calculating infiltration  - function which does not allow negative levels
        infilt_buf = infiltration.philip_infiltration(soil_type,h_new.reshape(r,c)/dt)
        infilt = ma.filled(infilt_buf,fill_value=0)
        # calculating residual for each cell
        for i in range(r):
            for j in range(c):
                # acumulation 
                res[j+i*c] += - (h_new[j+i*c] - h_old[j+i*c])/dt #m/s
                
                # rain 
                res[j+i*c] += act_rain[i][j] #m/s
                
                # sheet runoff
                res[j+i*c] += - sheet_flow[j+i*c] 
                
                # sheet inflows from neigbouring cells (try is used to avoid out of range errors)
                try:
                    res[j+i*c] +=  list_fd[j+i*c][0]*sheet_flow[(i-1)*c+j+1] #NE
                    # print(i,j,list_fd[j+i*c][0],sheet_flow[(i-1)*c+j+1],"NE")
                    # input()
                except:
                    pass   
                try:
                    res[j+i*c] +=  list_fd[j+i*c][1]*sheet_flow[(i-1)*c+j] #N
                    # print(i,j,list_fd[j+i*c][1],sheet_flow[(i-1)*c+j],"N")
                    # input()
                except:
                    pass 
                try:
                    res[j+i*c] +=  list_fd[j+i*c][2]*sheet_flow[(i-1)*c+j-1] #NW
                    # print(i,j,list_fd[j+i*c][2],sheet_flow[(i-1)*c+j-1],"NW")
                    # input()
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][3]*sheet_flow[(i)*c+j-1] #W
                    # print(i,j,list_fd[j+i*c][3],sheet_flow[(i)*c+j-1],"W")
                    # input()
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][4]*sheet_flow[(i+1)*c+j-1] #SW
                    # print(i,j,list_fd[j+i*c][4],sheet_flow[(i+1)*c+j-1],"SW")
                    # input()
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][5]*sheet_flow[(i+1)*c+j] #S
                    # print(i,j,list_fd[j+i*c][5],sheet_flow[(i+1)*c+j],"S")
                    # input()    
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][6]*sheet_flow[(i+1)*c+j+1] #SE
                    # print(i,j,list_fd[j+i*c][6],sheet_flow[(i+1)*c+j+1],    "SE")
                    # input()
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][7]*sheet_flow[(i)*c+j+1] #E
                    # print(i,j,list_fd[j+i*c][7],sheet_flow[(i)*c+j+1],"E")
                    # input()
                except:
                    pass
                    
                      
                # infiltration 
                res[j+i*c] += - infilt[i][j] 
                   
        return res

    # Method to performe one time step
    def do_next_h(self, surface, subsurface, rain_arr, cumulative, 
                  hydrographs, flow_control,  potRain, delta_t,list_fd):
        # global variables for infilitration
        global infilt_capa
        global max_infilt_capa
        global infilt_time
        # parameters
        r, c = GridGlobals.r, GridGlobals.c
        pixel_area = GridGlobals.get_pixel_area()
        fc = flow_control
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()
        # Calculating the infiltration
        # Until the max_infilt_capa
        infilt_capa += potRain
        if ma.all(infilt_capa < max_infilt_capa):
            infilt_time += delta_t
            actRain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )
            potRain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )
            
            return actRain

        # After the max_infilt_capa is filled       
        for iii in combinatIndex:
            # TODO: variable not used. Should we delete it?
            index = iii[0]
            k = iii[1]
            s = iii[2]
            
            iii[3] = infiltration.phlilip(
                k,
                s,
                delta_t,
                fc.total_time + delta_t -  infilt_time,
                NoDataValue)
        
        infiltration.set_combinatIndex(combinatIndex)
         

        # Calculating the actual rain
        actRain, fc.sum_interception, rain_arr.arr.veg = \
            rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)
        
        surface.arr.cur_rain = actRain

        # Upacking the old water level
        h_old = np.ravel(surface.arr.h_total_pre.tolist(0))
        
        # Changing the actRain to a list - inserting 0 for the NoDataValues	
        act_rain = (actRain/delta_t).tolist(0)
        # Extracting the smallest time step  - float insted of ma
        dt = delta_t.argmin()
        # Setting the initial guess for the solver
        
        h_0 = h_old 
        # Calculating the new water level
        soulution = sp.optimize.root(self.model, h_0, 
                                     args=(dt,
                                            h_old,
                                            list_fd,
                                            r,c,
                                            Globals.get_mat_aa(),Globals.get_mat_b(),
                                            act_rain,
                                            surface.arr.soil_type,
                                            pixel_area),
                                        method='krylov')
        
        h_new = soulution.x
        
        if soulution.success == False:
            print("Error: The solver did not converge")
            print("Objective function (vorst residual)= ", max(self.model(h_new,dt,
                                            h_old,
                                            list_fd,
                                            r,c,
                                            Globals.get_mat_aa(),Globals.get_mat_b(),
                                            act_rain,
                                            surface.arr.soil_type,
                                            pixel_area)))
            print("h_new = ",h_new)
            input("Press Enter to continue...")
        # Saving the new water level
        surface.arr.h_total_new = ma.array(h_new.reshape(r,c),mask=GridGlobals.masks) 

        # Saving results to surface structure (untidy solution) - looks akward, but don't cost much time to compute
        surface.arr.h_sheet = ma.copy(surface.arr.h_total_pre) # [m] - previous time stap as in the explicit version
        
        surface.arr.vol_runoff = sheet_runoff(Globals.get_mat_aa(), Globals.get_mat_b(), surface.arr.h_sheet)*dt #[m]        
        surface.arr.infiltration = infiltration.philip_infiltration(surface.arr.soil_type, surface.arr.h_total_new)*dt #[m]
            
         # Update the cumulative values
        cumulative.update_cumulative(
            surface.arr,
            subsurface.arr,
            delta_t)
        

        return actRain
                    
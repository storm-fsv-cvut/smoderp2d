# Main function of the preparation preparation package all date raster/vector
# or scalar are transfered to python line fashion numpy arrays are created to
# store spatially distributed parameters  digital elevation model
#
#  The computing area is determined  as well as the boundary cells.
#
#  \e prepare_data does the following:
#    - import data paths and input parameters
#    - do DEM preprocessing
#        - fill the DEM raster
#        - make flow direction raster
#        - make flow accumulation raster
#        - calculate slopes (percentage rise)
#        - make \e numpy arrays from rasters above
#    - identify the low left corner
#    - exclude the edge cells
#    - do the vector preprocessing
#        - check the attribute tables for parameters
#        - identify common area of input vector data
#        - identify common area of vector and raster data
#        - make \e numpy arrays the vector data
#
#  @param args sys.argv from the prompt or arcgis toolbox interface
#  @return \b boundaryRows stores all rows of raster where is a boundary located []
#  @return \b boundaryCols stores all columns of raster where is a boundary located [][]
#  @return \b mat_boundary array stores -99 at the boudary cells NoDataValue outside
#             the computational domain and zeros in the domain \e numpy[][]
#  @return \b rrows reduced rows - stores all rows of raster inside the domain []
#  @return \b rcols reduced columns - stores all columns of raster inside the domain [][]
#  @return \b ll_corner arcpy point coordinates of the main origin
#  @return \b x_coordinate x coordinate of the domain origin \e scalar
#  @return \b y_coordinate y coordinate of the domain origin
#  @return \b NoDataValue  no data value \e scalar
#  @return \b array_points position where time series of results is plotted [][]
#  @return \b rows all rows of the rasters
#  @return \b cols all columns of the rasters
#  @return \b combinatIndex prepare to assign the infiltration parameters [][]
#  @return \b delta_t  the time step \e scalar
#  @return \b mat_pi   array contains the potential clop interception   \e numpy[][]
#  @return \b mat_ppl  array contains the leaf area index \e numpy[][]
#  @return \b surface_retention  surface retention in meters \e scalar
#  @return \b mat_inf_index  array contains the infiltration indexes for the Philips infiltration  \e numpy[][]
#  @return \b mat_hcrit   array contain the critical height for the rill formation  \e numpy[][]
#  @return \b mat_aa   array contains the a parameter for the kinematic surface  runoff  \e numpy[][]
#  @return \b mat_b    array contains the b parameter for the kinematic surface  runoff  \e numpy[][]
#  @return \b mat_fd   array contains the the flow direction based of the arcpy.sa.FlowDirection \e numpy[][]
#  @return \b mat_dmt  array contains the the digital elevation model  based of the arcpy.sa.Fill \e numpy[][]
#  @return \b mat_efect_vrst  smer klonu???? #jj
#  @return \b mat_slope  array contains the slopes  based of the arcpy.sa.Slope \e numpy[][]
#  @return \b mat_nan   array contains the Not a Number values outside the domain \e numpy[][]
#  @return \b mat_a     ???? #jj
#  @return \b mat_n     array contains the \e n parameter for the rill calculation \e numpy[][]
#  @return \b output    output folder path \e string
#  @return \b pixel_area    area of the cell \e scalar
#  @return \b points     path to shapefile contains the points contains location of the time series
#  @return \b poradi     number of the columns in the parameter database  \e scalar
#  @return \b end_time     total time of the simulation \e scalar
#  @return \b spix  width of the raster cell \e scalar
#  @return \b vpix  height of the raster cell \e scalar
#  @return \b state_cell    array contains initial state of the cells  \e numpy[][]
#  @return \b temp   temporary files folder path \e string
#  @return \b type_of_computing   type of computing  \e string
#  @return \b mfda  set multi flow direction algorithm if true, default is D8 direction algorithm
#  @return \b sr  contains the rainfall data [][]
#  @return \b itera   amount of the rainfall intervals
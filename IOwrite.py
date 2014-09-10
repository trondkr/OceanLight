from datetime import datetime, timedelta
from netCDF4 import Dataset
from netCDF4 import num2date
import numpy as np
import time
import os

__author__   = 'Trond Kristiansen'
__email__    = 'trond.kristiansen@imr.no'
__created__  = datetime(2014, 1, 23)
__modified__ = datetime(2014, 1, 23)
__version__  = "0.1"
__status__   = "Development"


def help ():
     """
     This function generates a netCDF4 file and saves the runnings average values for
     specific years into file for each IPCC AR5 model.
     
     Used to gether with extractIce.py
     """

def writeCMIP5File(modelName,scenario,myvarname,lon,lat,time,mydata,mydataanomaly,outfilename):
    
     myformat='NETCDF3_CLASSIC'
     
     if os.path.exists(outfilename):
          os.remove(outfilename)
     print "Results written to netcdf file: %s"%(outfilename)
     if myvarname=="sic": myvar="SIC"
     
     f1 = Dataset(outfilename, mode='w', format=myformat)
     f1.title       = "IPCC AR5 %s"%(myvar)
     f1.description = "IPCC AR5 running averages of %s for model %s for scenario %s"%(myvar,modelName,scenario)
     f1.history     = "Created " + str(datetime.now())
     f1.source      = "Trond Kristiansen (trond.kristiansen@imr.no)"
     f1.type        = "File in NetCDF3 format created using iceExtract.py"
     f1.Conventions = "CF-1.0"

     """Define dimensions"""
     f1.createDimension('x',  len(lon))
     f1.createDimension('y', len(lat))
     f1.createDimension('time', None)
        
     vnc = f1.createVariable('longitude', 'd', ('x',),zlib=False)
     vnc.long_name = 'Longitude'
     vnc.units = 'degree_east'
     vnc.standard_name = 'longitude'
     vnc[:] = lon

     vnc = f1.createVariable('latitude', 'd', ('y',),zlib=False)
     vnc.long_name = 'Latitude'
     vnc.units = 'degree_north'
     vnc.standard_name = 'latitude'
     vnc[:] = lat

     v_time = f1.createVariable('time', 'd', ('time',),zlib=False)
     v_time.long_name = 'Years'
     v_time.units = 'Years'
     v_time.field = 'time, scalar, series'
     v_time[:]=time     
     
     v_temp=f1.createVariable('SIC', 'd', ('time', 'y', 'x',),zlib=False)
     v_temp.long_name = "Sea-ice area fraction (%)"
     v_temp.units = "%"
     v_temp.time = "time"
     v_temp.field="SIC, scalar, series"
     v_temp.missing_value = 1e20
     
    
     if myvarname=='sic':
          f1.variables['SIC'][:,:,:]  = mydata
          
     f1.close()

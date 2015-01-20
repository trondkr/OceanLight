from __future__ import division
import os, sys, datetime, string
import numpy as np
from netCDF4 import Dataset
import numpy.ma as ma
import calclight
import pandas as pd
cimport numpy as np
cimport cython

#cython: boundscheck=False
#cython: wraparound=False

DTYPE = np.double
ctypedef np.double_t DTYPE_t

__author__   = 'Trond Kristiansen'
__email__    = 'trond.kristiansen@imr.no'
__created__  = datetime.datetime(2010, 1, 16)
__modified__ = datetime.datetime(2014, 3, 4)
__version__  = "1.1"
__status__   = "Development, 16.01.2010, 14.04.2010, 04.03.2014"


def getMaxLight(lon,lat,year,month,day,icethickness,snowthickness,albedo,debug):
   
   dayOfYear=(datetime.datetime(year,month,day) - datetime.datetime(year, 1, 1)).days + 1
   
   # Calculate the maximum light possible for location
   radfl0=0.0; radmax=0.0; cawdir=0.0; clouds=0.0; daysinyear=365; sunHeight=0.0; surfaceLight=0.0
   lightAve,lightMax,cawdir = calclight.calclight.qsw(radfl0,radmax,cawdir,clouds, lat*np.pi/180.0,dayOfYear,daysinyear)
   
   # Calculate the light at noon
   hourOfDay=12;  # noon only
   maxLight = (1.0 - albedo)*lightAve # Convert from W/m2 to umol/m2/s-1 by dividing by : 0.217
   sunHeight, surfaceLight = calclight.calclight.surlig(hourOfDay,maxLight,dayOfYear,lat,sunHeight,surfaceLight)
  
   # Now calculate the amount of light below the sea ice and snow (Perovich 1996,
   # but see  Jin 2006 Annals of Glaciology)
   attenuationSnow = 20 #unit : m-1
   attenuationIceTop10cm = 5
   attenuationIceBelowSurface = 1
  
   Eb = surfaceLight
   if debug is True:
       print "\nSurface light for date: %s %s"%(dayOfYear, Eb)
   if snowthickness > 0:
       Eb = surfaceLight*np.exp(attenuationSnow*(-snowthickness))
       if debug is True:
           print "Eb with snow (%s m) : %s"%(snowthickness,Eb)

   if icethickness >= 0.1:
       Eb = Eb*np.exp(attenuationIceTop10cm*(-0.1))
       if debug is True:
           print "Eb with ice top (%s m) : %s"%(icethickness,Eb)
       Eb = Eb*np.exp(attenuationIceBelowSurface*(-(icethickness - 0.1)))
       if debug is True:
           print "Eb with ice below top (%s m) : %s"%(icethickness - 0.1,Eb)
   else:
        Eb = Eb*np.exp(attenuationIceTop10cm*(-icethickness))
        if debug is True:
            print "Eb with ice top (%s m) : %s"%(icethickness,Eb)


   return Eb


def calculateLight(np.ndarray[DTYPE_t, ndim=4] allData, dateobjects,np.ndarray[DTYPE_t, ndim=3] lightData, np.ndarray[DTYPE_t, ndim=3] lightDataMap,np.ndarray[DTYPE_t, ndim=2] lons,np.ndarray[DTYPE_t, ndim=2] lats,debug):
    
    cdef int dateN=np.shape(allData)[1]
    cdef int xN=np.shape(allData)[2]
    cdef int oldyear=-9
    cdef DTYPE_t Eb
    
    for dateindex in xrange(dateN):
        dateobject=dateobjects[dateindex]
        if dateobject.year > oldyear:
            print "Running year: %s"%(dateobject.year)
            oldyear=dateobject.year
         
        for x in xrange(xN):
            for y in xrange(np.shape(allData)[3]):
         
                sit = allData[0,dateindex,x,y]
                sic = allData[1,dateindex,x,y]
                snd = allData[2,dateindex,x,y]
                albedo = allData[3,dateindex,x,y]
                if albedo > 10: albedo=0.0
                lon = lons[x,y]
                lat = lats[x,y]
           
                Eb = getMaxLight(lon,lat,dateobject.year,dateobject.month,dateobject.day,sit,snd,albedo,debug)
                lightData[dateindex,x,y] = Eb
                if sic >0:
                    lightDataMap[dateindex,x,y] = Eb
                else:
                    lightDataMap[dateindex,x,y] = np.NaN
    return lightData, lightDataMap
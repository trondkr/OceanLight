from pylab import *
import matplotlib.dates as mdates

import os, sys, datetime, string
import numpy as np
from netCDF4 import Dataset
import time
import numpy.ma as ma
import calclight
from subprocess import call
import mpl_util
import pandas as pd
import calculateLightUnderIce
import prettyplotlib as ppl
import brewer2mpl

from mpl_toolkits.basemap import Basemap, interp, shiftgrid, addcyclic

import pyximport
pyximport.install(setup_args={'include_dirs':[np.get_include()]})


__author__   = 'Trond Kristiansen'
__email__    = 'trond.kristiansen@imr.no'
__created__  = datetime.datetime(2010, 1, 16)
__modified__ = datetime.datetime(2014, 3, 4)
__version__  = "1.1"
__status__   = "Development, 16.01.2010, 14.04.2010, 04.03.2014"

"""This script calculates the maximum and
average light irradiance (Wm-2) at given longitude
and latitude for a given date when the ice and snowthickness is known.
Wm-2 can be converted to umol/m2/s-1
by maxLight = maxLight/0.217


Compile :  A cython function which is found in the file calculateLightUnderIce.pyx is
    compiled with: python setup.py build_ext --inplace
"""




def remove_border(axes=None, top=False, right=False, left=True, bottom=True):
    """
    Minimize chartjunk by stripping out unnecesasry plot borders and axis ticks

    The top/right/left/bottom keywords toggle whether the corresponding plot border is drawn
    """
    ax = axes or plt.gca()
    ax.spines['top'].set_visible(top)
    ax.spines['right'].set_visible(right)
    ax.spines['left'].set_visible(left)
    ax.spines['bottom'].set_visible(bottom)

    #turn off all ticks
    ax.yaxis.set_ticks_position('none')
    ax.xaxis.set_ticks_position('none')

    #now re-enable visibles
    if top:
        ax.xaxis.tick_top()
    if bottom:
        ax.xaxis.tick_bottom()
    if left:
        ax.yaxis.tick_left()
    if right:
        ax.yaxis.tick_right()

def plotTimeseries(light,icethickness,snowthickness,lat):

    plot(icethickness,light)
    xlabel("Ice thickness (m)")
    ylabel("Light Wm-2")
    plotfile='figures/theoretical_ice_light_snowdepth_'+str(snowthickness)+'m_latitude_'+str(lat)+'.pdf'
    plt.savefig(plotfile,dpi=300,bbox_inches="tight",pad_inches=0)
    plt.clf()
    print 'Saved figure file %s\n'%(plotfile)
  #  plt.show()

def main():


    lon=15; year=2014; month=6; day=23;

    icethicknesslist=np.arange(0.1,4,0.01) #meter
    snowthicknesslist=np.arange(0,0.1,0.01) #meter
    latitudes=[70,80,90]
    light=[]
    albedo=0.9
    debug=False
    newfile=True
    for lat in latitudes:
        print "Calculating light for latitude: %s"%(lat)

        for ii in xrange(len(snowthicknesslist)):
            if (newfile):
                if not os.path.exists("THEORY"):
                    os.mkdir("THEORY/")
                outfilename="THEORY/theoretical_ice_light_snowthickness_"+str(snowthicknesslist[ii])+"m_latitue_"+str(lat)+".csv"
                out=open(outfilename,'a')
            for jj in xrange(len(icethicknesslist)):
                icethickness=icethicknesslist[jj]
                snowthickness=snowthicknesslist[ii]

                Eb = calculateLightUnderIce.getMaxLight(lon,lat,year,month,day,icethickness,snowthickness,albedo,debug)
                light.append(Eb)
                mydata = "%s, %s, %s, %s, %s, %s, %s, %s\n"%(lon, lat, month, day, albedo, icethickness, snowthickness, Eb)
                out.writelines(mydata)
            jj=0
            out.close()
            newfile=True
            plotTimeseries(light,icethicknesslist,snowthickness,lat)
            light=[]

main()         
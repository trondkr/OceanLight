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

def calculateArea(lat0,lat1,lon0,lon1,areaIce):

    earthRadius = 6371000
    rad = np.pi / 180.0

    """    -180 <= lon0 < lon1 <= 180
            -90 <= lat0 < lat1 <= 90
            areaIce is in percent
    """

    area = earthRadius**2 * (np.sin(lat1*rad)-np.sin(lat0*rad)) * (lon1 - lon0) * rad

    return area * (areaIce)


"""Function that opens a CMIP5 file and reads the contents. The innput
is assumed to be on grid 0-360 so all values are shifted to new grid
on format -180 to 180 using the shiftgrid function of basemap."""
def openCMIP5file(myvar,CMIP5Hist,CMIP5Proj,first):

    if os.path.exists(CMIP5Hist):
        myfileHist=Dataset(CMIP5Hist)
        print "Opened CMIP5 file: %s"%(CMIP5Hist)
    else:
        print "Could not find CMIP5 input file %s : abort"%(CMIP5Hist)
        print "Make sure that needToSubsetData is set to False if you have no data in SUBSET folder"
        sys.exit()

    if os.path.exists(CMIP5Proj):
        myfileProj=Dataset(CMIP5Proj)
        print "Opened CMIP5 file: %s"%(CMIP5Proj)
    else:
        print "Could not find CMIP5 input file %s : abort"%(CMIP5Proj)
        print "Make sure that needToSubsetData is set to False if you have no data in SUBSET folder"
        sys.exit()

    dateobjects=[]; timeFull=[]
    if first is True:
        timeHist=myfileHist.variables["time"][:]
        timeProj=myfileProj.variables["time"][:]
        refDateH=myfileHist.variables["time"].units
        refDateP=myfileProj.variables["time"].units

        refdateProj=datetime.datetime(int(refDateP[11:15]),1,1,0,0,0)
        refdateHist=datetime.datetime(int(refDateH[11:15]),1,1,0,0,0)

        startH=refdateHist + datetime.timedelta(days=float(timeHist[0]))
        endH=refdateHist + datetime.timedelta(days=float(timeHist[-1]))
        startP=refdateProj + datetime.timedelta(days=float(timeProj[0]))
        endP=refdateProj + datetime.timedelta(days=float(timeProj[-1]))
        if first is True:
            print "Found Historical to start in year %s and end in %s"%(startH.year,endH.year)
            print "Found Projections to start in year %s and end in %s"%(startP.year,endP.year)

        """Create the datetime objects for pandas"""

        for t in timeHist:
            dateobjects.append(refdateHist + datetime.timedelta(days=t))
        for t in timeProj:
            dateobjects.append(refdateProj + datetime.timedelta(days=t))

        """Combine the time arrays"""
        timeFull = np.ma.concatenate((timeHist,timeProj),axis=0)

    myTEMPHIST=np.squeeze(myfileHist.variables[myvar][:])
    myTEMPHIST=np.ma.masked_where(myTEMPHIST==myTEMPHIST.fill_value,myTEMPHIST)
    myTEMPPROJ=np.squeeze(myfileProj.variables[myvar][:])
    myTEMPPROJ=np.ma.masked_where(myTEMPPROJ==myTEMPHIST.fill_value,myTEMPPROJ)

    lonCMIP5=np.squeeze(myfileHist.variables["lon"][:])
    latCMIP5=np.squeeze(myfileHist.variables["lat"][:])

    """Combine the myvarname arrays"""
    dataFull = np.ma.concatenate((myTEMPHIST,myTEMPPROJ),axis=0)
    """Make sure that we have continous data around the globe"""
    dataFull, loncyclicCMIP5 = addcyclic(dataFull, lonCMIP5)
    lons,lats=np.meshgrid(loncyclicCMIP5,latCMIP5)

    return dateobjects, timeFull, dataFull, lons, lats


"""Map related functions:"""
def plotMap(lon,lat,mydata,modelName,scenario,mydate):

    plt.figure(figsize=(12,12),frameon=False)
    mymap = Basemap(projection='npstere',lon_0=0,boundinglat=50)

    x, y = mymap(lon,lat)
    levels=np.arange(np.min(mydata),np.max(mydata),1)

    CS1 = mymap.contourf(x,y,mydata,levels,
                         cmap=mpl_util.LevelColormap(levels,cmap=cm.RdBu_r),
                         extend='max',
                         antialiased=False)

    mymap.drawparallels(np.arange(-90.,120.,15.),labels=[1,0,0,0]) # draw parallels
    mymap.drawmeridians(np.arange(0.,420.,30.),labels=[0,1,0,1]) # draw meridians

    mymap.drawcoastlines()
    mymap.drawcountries()
    mymap.fillcontinents(color='grey')
    plt.colorbar(CS1,shrink=0.5)
    title('Model:'+str(modelName)+' Year:'+str(mydate.year)+' Month:'+str(mydate.month))

    CS1.axis='tight'
    plt.show()
    if not os.path.exists("Figures"):
        os.mkdir("Figures/")
    plotfile='figures/map_light_'+str(modelName)+'_'+str(mydate.year)+'_'+str(mydate.month)+'.png'
    plt.savefig(plotfile,dpi=300)
    plt.clf()
    plt.close()



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

def plotTimeseries(ts,myvar):

    ts_annual = ts.resample("A")
    ts_quarterly = ts.resample("Q")
    ts_monthly = ts.resample("M")

    # Write data to file
    mypath="%s_annualaverages.csv"%(myvar)
    if os.path.exists(mypath):os.remove(mypath)
    ts.to_csv(mypath)
    print "Wrote timeseries to file: %s"%(mypath)

    red_purple = brewer2mpl.get_map('RdPu', 'Sequential', 9).mpl_colormap
    colors = red_purple(np.linspace(0, 1, 12))
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111)
   # for mymonth in xrange(12):
        #ts[(ts.index.month==mymonth+1)].plot(marker='o', color=colors[mymonth],markersize=5, linewidth=0,alpha=0.8)
    #hold(True)
    ts_annual.plot(marker='o', color="#FA9D04", linewidth=0,alpha=1.0, markersize=7, label="Annual")
    remove_border(top=False, right=False, left=True, bottom=True)
    #ts_monthly.plot(style="r", marker='o', linewidth=1,label="Monthly")

    # legend(loc='best')
    ylabel(r'Light (W m$^{-2})$')

    plotfile='figures/timeseries_'+str(myvar)+'.pdf'
    plt.savefig(plotfile,dpi=300,bbox_inches="tight",pad_inches=0)
    print 'Saved figure file %s\n'%(plotfile)
    plt.show()

def main():

    scenarios=["RCP85"]
    needToSubsetData=True

    myvars=["sit","sic","snd","ialb"] # order is important
    debug=False

    yearsToExtract=np.arange(1850,2100,1)

    for scenario in scenarios:
        print "-----------------------"
        print "Running scenario: %s"%(scenario)
        print "-----------------------"
        first=True
        counter=0

        for myvar in myvars:

            modelRCP  = "%s_OImon_NorESM1-M_%s_r1i1p1_200601-210012_rectangular.nc"%(myvar,scenario.lower())
            modelHIST = "%s_OImon_NorESM1-M_historical_r1i1p1_185001-200512_rectangular.nc"%(myvar)
            modelName  = "NorESM1-M"


            print "-----------------------------------\n"
            print "Extracting data from model: %s   "%(modelName)
            print "-----------------------------------\n"


            workDir="/Users/trondkr/Projects/RegScen/NorESM/%s/"%(scenario.upper())
            workDirHist="/Users/trondkr/Projects/RegScen/NorESM/Historical/"

            CMIP5file=workDir+modelRCP
            CMIP5HISTfile=workDirHist+modelHIST

            """Prepare output file:"""
            """Save filenames and paths for creating output filenames"""

            if not os.path.exists("SUBSET"):
                os.mkdir("SUBSET/")
            outfilenameProj="SUBSET/"+os.path.basename(CMIP5file)[0:-4]+"_Arctic.nc"
            outfilenameHist="SUBSET/"+os.path.basename(CMIP5HISTfile)[0:-4]+"_Arctic.nc"

            if needToSubsetData is True:
                call(["cdo","sellonlatbox,0,360,60,90",CMIP5file,outfilenameProj])
                call(["cdo","sellonlatbox,0,360,60,90",CMIP5HISTfile,outfilenameHist])

            dateobjects, timeFull, dataFull, lons, lats = openCMIP5file(myvar,outfilenameHist,outfilenameProj,first)
            if first is True:
                allData=np.zeros((4,np.shape(dataFull)[0],np.shape(dataFull)[1],np.shape(dataFull)[2]))
                lightData=np.zeros((np.shape(dataFull)[0],np.shape(dataFull)[1],np.shape(dataFull)[2]))
                lightDataMap=np.zeros((np.shape(dataFull)[0],np.shape(dataFull)[1],np.shape(dataFull)[2]))
                allTime=timeFull
                allDateObjects=dateobjects
                first=False

            """Store all datavariables into one big array for easy access when looping afterwards"""
            allData[counter,:,:,:] = dataFull
            counter+=1

            print "Finished storring all data into large array of shape:",np.shape(allData)

    """Now loop over each grid cell for all time-steps to caluclate the light in each cell"""
    oldyear=-999

    """The following is cython function which is found in the file calculateLightUnderIce.pyx and
    compile with: python setup.py build_ext --inplace"""

    allDateObjects=np.asarray(allDateObjects)
    lightData, lightDataMap = calculateLightUnderIce.calculateLight(allData,allDateObjects,lightData,lightDataMap,lons,lats,debug)
    #  lightDataMap = np.ma.masked_invalid(lightDataMap)
    # plotMap(lons,lats,np.squeeze(lightDataMap[dateindex,:,:]),modelName,scenario,dateobject)
    timeseriesLight=[]
    for dateindex in xrange(np.shape(allData)[1]):
        timeseriesLight.append(np.mean(lightData[dateindex,:,:]))

    ts=pd.Series(timeseriesLight,allDateObjects)

    plotTimeseries(ts,"light")

main()         
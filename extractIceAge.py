
import numpy as np
from pylab import *
import string, os, sys
import datetime, types
from netCDF4 import Dataset
from subprocess import call
import mpl_util
import pandas as pd
import IOwrite
import prettyplotlib as ppl
import brewer2mpl

from mpl_toolkits.basemap import Basemap, interp, shiftgrid, addcyclic
import datetime as datetime

__author__   = 'Trond Kristiansen'
__email__    = 'me (at) trondkristiansen.com'
__created__  = datetime.datetime(2014, 1, 23)
__modified__ = datetime.datetime(2014, 1, 23)
__version__  = "1.0"
__status__   = "Production"

"""This script reads
Input files that need to be created using:
cdo genbil,r360x180 ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012.nc ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012_wgts.nc
cdo remap,r360x180,ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012_wgts.nc ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012.nc ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012_rectangular.nc

Next, this script will call the following command on the output:
cdo sellonlatbox,0,360,-60,-90 filename.in.nc filename.out.nc 
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
         
def plotTimeseries(ts,myvar):
    
    ts_annual = ts.resample("A")
    ts_quarterly = ts.resample("Q")
    ts_monthly = ts.resample("M")


    red_purple = brewer2mpl.get_map('RdPu', 'Sequential', 9).mpl_colormap
    colors = red_purple(np.linspace(0, 1, 12))
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111)
    mypath="%s_annualaverages.csv"%(myvar)
    if os.path.exists(mypath):os.remove(mypath)
    ts.to_csv(mypath)
    #for mymonth in xrange(12):
    #    ts[(ts.index.month==mymonth+1)].plot(marker='o', color=colors[mymonth],markersize=5, linewidth=0,alpha=0.8)
    #
    #    hold(True)
    ts_annual.plot(marker='o', color="#FA9D04", linewidth=0,alpha=1.0, markersize=7, label="Annual")
    
    remove_border(top=False, right=False, left=True, bottom=True)
    
    ylabel('Iceage (years)')
      
    plotfile='figures/timeseries_'+str(myvar)+'.pdf'
    plt.savefig(plotfile,dpi=300,bbox_inches="tight",pad_inches=0)
    print 'Saved figure file %s\n'%(plotfile)
    plt.show()
    
"""Function that opens a CMIP5 file and reads the contents. The innput
is assumed to be on grid 0-360 so all values are shifted to new grid
on format -180 to 180 using the shiftgrid function of basemap."""
def openCMIP5file(selectedMonth,useSmoothing,CMIP5Hist,CMIP5Proj,myvar,yearsOfSmoothing,yearsToExtract,modelName,scenario,outfilenameResults):

    if os.path.exists(CMIP5Hist):
        myfileHist=Dataset(CMIP5Hist)
        print "Opened CMIP5 file: %s"%(CMIP5Hist)
    else:
        print "Could not find CMIP5 input file %s : abort"%(CMIP5Hist)
        sys.exit()

    if os.path.exists(CMIP5Proj):
        myfileProj=Dataset(CMIP5Proj)
        print "Opened CMIP5 file: %s"%(CMIP5Proj)
    else:
        print "Could not find CMIP5 input file %s : abort"%(CMIP5Proj)
        sys.exit()
        
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

    print "Found Historical to start in year %s and end in %s"%(startH.year,endH.year)
    print "Found Projections to start in year %s and end in %s"%(startP.year,endP.year)

    """Now extract the data for given year"""
    if myvar=="ageice":
        myTEMPHIST=np.squeeze(myfileHist.variables[myvar][:])
       
        myTEMPHIST=np.ma.masked_where(myTEMPHIST==myTEMPHIST.fill_value,myTEMPHIST)
        myTEMPPROJ=np.squeeze(myfileProj.variables[myvar][:])
        myTEMPPROJ=np.ma.masked_where(myTEMPPROJ==myTEMPHIST.fill_value,myTEMPPROJ)
      
        
    lonCMIP5=np.squeeze(myfileHist.variables["lon"][:])
    latCMIP5=np.squeeze(myfileHist.variables["lat"][:])
    
    """Combine the time arrays"""
    timeFull = np.ma.concatenate((timeHist,timeProj),axis=0)
    """Combine the myvarname arrays"""
    dataFull = np.ma.concatenate((myTEMPHIST,myTEMPPROJ),axis=0)
    """Make sure that we have continous data around the globe"""
    dataFull, loncyclicCMIP5 = addcyclic(dataFull, lonCMIP5)
    lons,lats=np.meshgrid(loncyclicCMIP5,latCMIP5)
    
    """Create the datetime objects for pandas"""
    mydates=[]
    for t in timeHist:
        mydates.append(refdateHist + datetime.timedelta(days=t))
    for t in timeProj:
        mydates.append(refdateProj + datetime.timedelta(days=t))
    
    """Calculate the climatology 1961-1990"""
    startI=False; endI=False; startIndex=-99; endIndex=99999999
    for index,mydate in enumerate(mydates):
        if startI==False and mydate.year==1961:
            startIndex=index
            startI=True
        if endI==False and mydate.year==1990:
            endIndex=index
            endI=True
        
    print "Climatology will be calculated for period: %s to %s"%(mydates[startIndex].year, mydates[endIndex].year)
    climatology=np.ma.zeros((dataFull.shape[1],dataFull.shape[2]))
    
    for i in xrange(dataFull.shape[1]):
        for j in xrange(dataFull.shape[2]):
            climatology[i,j]=np.ma.mean(dataFull[startIndex:endIndex,i,j])
         
    
    """Calculate running mean for entire timeseries"""
    dataSmooth=np.ma.zeros(np.shape(dataFull))
    
    """Now extract only the data for the years we ware interested in saving to file:"""
    dataSmoothSelected=np.ma.zeros((len(yearsToExtract)*12+1,dataSmooth.shape[1],dataSmooth.shape[2]), dtype=np.float)
    iceArea=[]
    iceTime=[]  
    counter=0
  
    for index,mydate in enumerate(mydates):
        
        if (mydate.year in yearsToExtract):
            
            dataSmoothSelected[counter,:,:]=dataFull[index,:,:]
            dataSmoothSelected[counter,:,:]=np.ma.masked_invalid(dataSmoothSelected[counter,:,:])
            
          #  if mydate.month == selectedMonth:
               # plotMap(lons,lats,np.ma.masked_invalid(dataSmoothSelected[counter,:,:]),modelName,scenario,mydate,"regular")
                #print " -> Extracted data for year/month %s/%s - %3.3f"%(mydate.year,mydate.month,np.sum(dataSmoothSelected[counter,:,:])-np.sum(climatology))
                 
            iceArea.append(calculateTotalIceArea(mydate.month,mydate.year,dataSmoothSelected[counter,:,:],loncyclicCMIP5,latCMIP5))
            iceTime.append(mydate)
            
            counter+=1
    
    ts=pd.Series(iceArea,iceTime)
    
    plotTimeseries(ts,"iceage")
  
    
"""Map related functions:"""
def plotMap(lon,lat,mydata,modelName,scenario,mydate,mytype):
     
    plt.figure(figsize=(12,12),frameon=False)
    mymap = Basemap(projection='npstere',lon_0=0,boundinglat=65)

    x, y = mymap(lon,lat)
    if mytype=="anomalies":
        levels=np.arange(np.min(mydata),np.max(mydata),1)
        #levels=np.arange(-2,5,0.1)
    else:
        levels=np.arange(np.min(mydata),np.max(mydata),5)
        #levels=np.arange(-2,15,0.5)
    
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
    if (mytype=="anomalies"):
        title('Model:'+str(modelName)+' Year:'+str(mydate.year)+' Month:'+str(mydate.month))
 
    if (mytype=="regular"):
        title('Model:'+str(modelName)+' Year:'+str(mydate.year)+' Month:'+str(mydate.month))
 
 
    #CS1.axis='tight'
    #plt.show()
    if not os.path.exists("Figures"):
            os.mkdir("Figures/")
    if (mytype=="anomalies"):
        plotfile='figures/map_anomalies_'+str(modelName)+'_'+str(mydate.year)+'_'+str(mydate.month)+'.png'
    else:
        plotfile='figures/map_'+str(modelName)+'_'+str(mydate.year)+'_'+str(mydate.month)+'.png'
    plt.savefig(plotfile,dpi=300)
    plt.clf()
    plt.close()
    #
 
def calculateTotalIceArea(month,year,icedata,lon,lat):
    
    icethickness = np.mean(icedata)
    print "Total mean ice thickness for month: %s year: %s -> %s "%(month,year,icethickness)
    
    return icethickness
          
        

def main():

    """Decide on what variable and LME to use:"""
    var="SeaIceAge"
    yearsOfSmoothing=1
    useSmoothing=False

    scenarios=["RCP85"]
    selectedMonths=[9]
    
    yearsToExtract=np.arange(1850,2100,1)
    if var=="SeaIceAge": myvarname="ageice"
    
    for selectedMonth in selectedMonths:
        for scenario in scenarios:
            print "-----------------------"
            print "Running scenario: %s"%(scenario)
            print "-----------------------"
            if var=="SeaIceAge":
                
                if scenario=="RCP85":
                    modelsRCP = ["ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012_rectangular.nc"]
        
                modelsHIST  = ["ageice_OImon_NorESM1-M_historical_r1i1p1_185001-200512_rectangular.nc"]
                modelNames  = ["NorESM1-M"]
        
          
            """Loop over all models of interest:"""
            for index in xrange(len(modelsRCP)):
                print "------------------------------\n"
                print "Extracting data from model: %s"%(modelNames[index])
                print "------------------------------\n"
        
        
                if var=="SeaIceAge":
                    if scenario=="RCP85":
                        workDir="/Users/trondkr/Projects/RegScen/NorESM/RCP85/"
                    workDirHist="/Users/trondkr/Projects/RegScen/NorESM/Historical/"
        
                CMIP5file=workDir+modelsRCP[index]
                CMIP5HISTfile=workDirHist+modelsHIST[index]
        
                """Prepare output file:"""
                """Save filenames and paths for creating output filenames"""
             
                if not os.path.exists("SUBSET"):
                    os.mkdir("SUBSET/")
                outfilenameProj="SUBSET/"+os.path.basename(CMIP5file)[0:-4]+"_Arctic.nc"
                outfilenameHist="SUBSET/"+os.path.basename(CMIP5HISTfile)[0:-4]+"_Arctic.nc"
              
                call(["cdo","sellonlatbox,0,360,60,90",CMIP5file,outfilenameProj])
                call(["cdo","sellonlatbox,0,360,60,90",CMIP5HISTfile,outfilenameHist])
                
                if not os.path.exists("RESULTS"):
                    os.mkdir("RESULTS/")
                outfilenameResults="RESULTS/"+os.path.basename(CMIP5file)[0:-4]+"_Arctic_runningMeanSelectedYears.nc"
                openCMIP5file(selectedMonth,useSmoothing,outfilenameHist,outfilenameProj,myvarname,yearsOfSmoothing,yearsToExtract,modelNames[index],scenario,outfilenameResults)
                
                
                

main()
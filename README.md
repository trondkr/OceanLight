OceanLight
==========
<h2>Ocean light toolbox</h2>
A suite of Python, Fortran, and Cython scripts have been created to make it easy to extract specific data from Earth System Model (ESM) results and to further use these data in combination to calculate light conditions in the ocean. 

<h3>Toolbox main programs</h3>
<ul>
<li><b>extractIce.py</b> - extract ice coverage data for region and create timeseries</li>
<li><b>extractIceThickness.py</b> - extract ice thickness for region and create timeseries</li>
<li><b>extractIceAge.py</b> - extract the age of ice for region and create timeseries</li>
<li><b>calculateMaxLight.py</b> - Calculate light at depth in water column under sea ice and snow for region and create timeseries</li>
</ul>

<h3>Supplemental programs required to run the main programs</h3>
<ul>
<li><b>extractLightUnderIce.pyx</b> - Cython program for doing the core calculations using C for speed</li>
<li><b>setup.py</b> - compiles the Cython program</li>
<li><b>calclight.f90</b> - Fortran program that calculates the maximum surface light for a given longitude-latitude and time of year (used by extractLightUnderIce.pyx)</li>
</ul>

<h3>Plot maps and time-series</h3>
The Python programs also contain routines for plotting the results of the calculations and data extractions. Time-series are created from extracting the data for the region of interest for the time period of interest and then modified using the Pandas module to plot annual time-series

Maps can be created using the Basemap module where the data plotted is either anomalies relative to a climatology or the actual data.

```Python
def plotMap(lon,lat,mydata,modelName,scenario,mydate,mytype):
    plt.figure(figsize=(12,12),frameon=False)
    mymap = Basemap(projection='npstere',lon_0=0,boundinglat=65)

    x, y = mymap(lon,lat)
    levels=np.arange(np.min(mydata),np.max(mydata),1)
    
    CS1 = mymap.contourf(x,y,mydata,levels,
                       cmap=mpl_util.LevelColormap(levels,cmap=cm.RdBu_r),
                       extend='max',
                       antialiased=False)
    
    mymap.drawcoastlines()
    mymap.drawcountries()
    mymap.fillcontinents(color='grey')
    plt.colorbar(CS1,shrink=0.5)
    plt.show()
``` 

 <figure>
  <img src="http://www.trondkristiansen.com/wp-content/gallery/romstools/map_NorESM1-M_2011_9.png" width=80% height=80%> 
  <figcaption>Ice concentration for September 2011 as calculated by NorESM .</figcaption>
</figure> 

Simple time-series are plotted by sending the method a Pandas time-series object:
  
```Python      
def plotTimeseries(ts, myvar):
    
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
    ts_annual.plot(marker='o', color="#FA9D04", linewidth=0,alpha=1.0, markersize=7, label="Annual")
  
    ylabel('Iceage (years)')
    plt.show()
``` 

<h2>Installation</h2>
The toolbox for calculating light at depth in the ocean under sea-ice and snow uses a combination of Python, Fortran and Cython. The main program is `calculateMaxLight.py` which calculates the maximum and average light irradiance (Wm-2) at given longitude and latitude for a given date when the ice and snowthickness is known. Wm-2 can be converted to umol/m2/s-1 by maxLight = maxLight/0.217. The program calls a Cython program called `calculateLightUnderIce.pyx` which you have to compile using the accompanying `setup.py` script.

``` python
python setup.py build_ext --inplace
```

To run the programs you also need historical and future projections of sea-ice dynamics. In my case I used the <a href="http://folk.uib.no/ngfhd/EarthClim/index.htm#en" target="_blank">NorESM</a> model results which I first converted to a rectangular grid using the <a href="https://code.zmaw.de/projects/cdo" target="_blank"> CDO</a> (climate data operators). As an example, to convert input files to a rectangular grid combine cdo commands like this:

``` bash
cdo genbil,r360x180 ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012.nc ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012_wgts.nc
cdo remap,r360x180,ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012_wgts.nc ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012.nc ageice_OImon_NorESM1-M_rcp85_r1i1p1_200601-210012_rectangular.nc
```

Next, to extract the area (e.g. 0-360E, 60-90N)of the global files you are interested in extract the data using:

``` bash
cdo sellonlatbox,0,360,60,90 filename.in.nc filename.out.nc 
```

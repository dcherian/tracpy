"""
Plotting routines for tracking.

Functions include:
* background
* hist
* tracks
"""

import matplotlib as mpl
mpl.use("Agg") # set matplotlib to use the backend that does not require a windowing system
import numpy as np
from mpl_toolkits.basemap import Basemap
from matplotlib.mlab import *
from matplotlib.pyplot import *
import inout
import os
import pdb
import matplotlib.ticker as ticker
import op
import netCDF4 as netCDF
import tools

def background(grid=None, ax=None, pars=np.arange(18, 35), mers=np.arange(-100, -80), 
                hlevs=np.hstack(([10,20],np.arange(50,500,50))), 
                col='lightgrey', fig=None, outline=True, merslabels=[0, 0, 0, 1],
                parslabels=[1, 0, 0, 0]):
    """
    Plot basic TXLA shelf background: coastline, bathymetry, meridians, etc
    Can optionally input grid (so it doesn't have to be loaded again)

    pars    parallels to plot
    mers    meridians to plot
    hlevs   which depth contours to plot
    """

    # matplotlib.rcParams.update({'font.size': 18})#,'font.weight': 'bold'})

    if grid is None:
        loc = 'http://barataria.tamu.edu:8080/thredds/dodsC/NcML/txla_nesting6.nc'
        grid = inout.readgrid(loc)

    if fig is None:
        fig = gcf()

    if ax is None:
        ax = gca()

    # Do plot
    try:
        grid['basemap'].drawcoastlines(ax=ax)
        grid['basemap'].fillcontinents('0.8',ax=ax)
        grid['basemap'].drawparallels(pars, dashes=(1, 1),
                                      linewidth=0.15, labels=parslabels, ax=ax)
        grid['basemap'].drawmeridians(mers, dashes=(1, 1),
                                      linewidth=0.15, labels=merslabels, ax=ax)
        # hold('on')
    except AttributeError:
        print('Ignoring basemap directive')

    ax.contour(grid['xr'], grid['yr'], grid['h'], hlevs,
               colors=col, linewidths=0.5)

    if outline:
        # Outline numerical domain
        ax.plot(grid['xr'][0,:], grid['yr'][0,:], 'k:')
        ax.plot(grid['xr'][-1,:], grid['yr'][-1,:], 'k:')
        ax.plot(grid['xr'][:,0], grid['yr'][:,0], 'k:')
        ax.plot(grid['xr'][:,-1], grid['yr'][:,-1], 'k:')


def hist(lonp, latp, fname, tind='final', which='contour', vmax=None, fig=None, ax=None, \
            bins=(40,40), N=10, grid=None, xlims=None, ylims=None, C=None, Title=None,
            weights=None, Label='Final drifter location (%)', isll=True, binscale=None):
    """
    Plot histogram of given track data at time index tind.

    Inputs:
        lonp,latp   Drifter track positions in lon/lat [time x ndrifters]
        fname       Plot name to save
        tind        (optional) Default is 'final', in which case the final
                    position of each drifter in the array is found
                    and plotted. Alternatively, a time index 
                    can be input and drifters at that time will be plotted.
                    Note that once drifters hit the outer numerical boundary,
                    they are nan'ed out so this may miss some drifters.
        which       (optional) 'contour', 'pcolor', 'hexbin', 'hist2d' 
                    for type of plot used. Default 'hexbin'.
        bins        (optional) Number of bins used in histogram. Default (15,25).
        N           (optional) Number of contours to make. Default 10.
        grid        (optional) grid as read in by inout.readgrid()
        xlims       (optional) value limits on the x axis
        ylims       (optional) value limits on the y axis
        isll        Default True. Inputs are in lon/lat. If False, assume they 
                    are in projected coords.

    Note: Currently assuming we are plotting the final location 
    of each drifter regardless of tind.
    """

    if grid is None:
        loc = 'http://barataria.tamu.edu:8080/thredds/dodsC/NcML/txla_nesting6.nc'
        grid = inout.readgrid(loc)

    if isll: # if inputs are in lon/lat, change to projected x/y
        # Change positions from lon/lat to x/y
        xp, yp = grid['basemap'](lonp, latp)
        # Need to retain nan's since basemap changes them to values
        ind = np.isnan(lonp)
        xp[ind] = np.nan
        yp[ind] = np.nan
    else:
        xp = lonp
        yp = latp

    if fig is None:
        fig = figure(figsize=(11,10))
    else:
        fig = fig
    background(grid) # Plot coastline and such

    # pdb.set_trace()

    if tind == 'final':
        # Find final positions of drifters
        xpc, ypc = tools.find_final(xp, yp)
    elif is_numlike(tind):
        xpc = xp[:,tind]
        ypc = yp[:,tind]
    else: # just plot what is input if some other string
        xpc = xp.flatten()
        ypc = yp.flatten()

    if which == 'contour':

        # Info for 2d histogram
        H, xedges, yedges = np.histogram2d(xpc, ypc,
                                range=[[grid['xr'].min(), \
                                grid['xr'].max()], \
                                [grid['yr'].min(), \
                                grid['yr'].max()]],
                                bins=bins)
        # Contour Plot
        XE, YE = np.meshgrid(op.resize(xedges,0), op.resize(yedges,0))
        d = (H/H.sum())*100
        # # from http://matplotlib.1069221.n5.nabble.com/question-about-contours-and-clim-td21111.html
        # locator = ticker.MaxNLocator(50) # if you want no more than 10 contours
        # locator.create_dummy_axis()
        # locator.set_bounds(0,1)#d.min(),d.max())
        # levs = locator()
        con = contourf(XE, YE, d.T, N)#,levels=levs)#(0,15,30,45,60,75,90,105,120))
        con.set_cmap('YlOrRd')

        if Title is not None:
            set_title(Title)

        # Horizontal colorbar below plot
        cax = fig.add_axes([0.3725, 0.25, 0.48, 0.02]) #colorbar axes
        cb = colorbar(con, cax=cax, orientation='horizontal')
        cb.set_label('Final drifter location (percent)')

        # Save figure into a local directory called figures. Make directory if it doesn't exist.
        if not os.path.exists('figures'):
            os.makedirs('figures')

        savefig('figures/' + fname + 'histcon.png',bbox_inches='tight')
        # savefig('figures/' + fname + 'histcon.pdf',bbox_inches='tight')

    elif which == 'pcolor':

        # Info for 2d histogram
        H, xedges, yedges = np.histogram2d(xpc, ypc,
                                range=[[grid['xr'].min(), \
                                grid['xr'].max()], \
                                [grid['yr'].min(), \
                                grid['yr'].max()]],
                                bins=bins, weights=weights)
        # print H.T.max()

        # pdb.set_trace()
        # Pcolor plot
        
        # C is the z value plotted, and is normalized by the total number of drifters
        if C is None:
            C = (H.T/H.sum())*100
        else:
            # or, provide some other weighting
            C = (H.T/C)*100

        p = pcolor(xedges, yedges, C, cmap='YlOrRd')

        if Title is not None:
            set_title(Title)

        # Set x and y limits
        # pdb.set_trace()
        if xlims is not None:
            xlim(xlims)
        if ylims is not None:
            ylim(ylims)

        # Horizontal colorbar below plot
        cax = fig.add_axes([0.3775, 0.25, 0.48, 0.02]) #colorbar axes
        cb = colorbar(p, cax=cax, orientation='horizontal')
        cb.set_label('Final drifter location (percent)')

        # Save figure into a local directory called figures. Make directory if it doesn't exist.
        if not os.path.exists('figures'):
            os.makedirs('figures')

        savefig('figures/' + fname + 'histpcolor.png', bbox_inches='tight')
        # savefig('figures/' + fname + 'histpcolor.pdf',bbox_inches='tight')

    elif which == 'hexbin':


        if ax is None:
            ax = gca()
        else:
            ax = ax
        
        if C is None:
            # C with the reduce_C_function as sum is what makes it a percent
            C = np.ones(len(xpc))*(1./len(xpc))*100
        else:
            C = C*np.ones(len(xpc))*100
        hb = hexbin(xpc, ypc, C=C, cmap='YlOrRd', gridsize=bins[0], 
                extent=(grid['xpsi'].min(), grid['xpsi'].max(), 
                grid['ypsi'].min(), grid['ypsi'].max()), 
                reduce_C_function=sum, vmax=vmax, axes=ax, bins=binscale)

        # Set x and y limits
        # pdb.set_trace()
        if xlims is not None:
            xlim(xlims)
        if ylims is not None:
            ylim(ylims)

        if Title is not None:
            ax.set_title(Title)

        # Want colorbar at the given location relative to axis so this works regardless of # of subplots, 
        # so convert from axis to figure coordinates
        # To do this, first convert from axis to display coords
        # transformations: http://matplotlib.org/users/transforms_tutorial.html
        ax_coords = [0.35, 0.25, 0.6, 0.02] # axis: [x_left, y_bottom, width, height]
        disp_coords = ax.transAxes.transform([(ax_coords[0],ax_coords[1]),(ax_coords[0]+ax_coords[2],ax_coords[1]+ax_coords[3])]) # display: [x_left,y_bottom,x_right,y_top]
        inv = fig.transFigure.inverted() # inverter object to go from display coords to figure coords
        fig_coords = inv.transform(disp_coords) # figure: [x_left,y_bottom,x_right,y_top]
        # actual desired figure coords. figure: [x_left, y_bottom, width, height]
        fig_coords = [fig_coords[0,0],fig_coords[0,1],fig_coords[1,0]-fig_coords[0,0],fig_coords[1,1]-fig_coords[0,1]]
        # Inlaid colorbar
        cax = fig.add_axes(fig_coords)

        # # Horizontal colorbar below plot
        # cax = fig.add_axes([0.3775, 0.25, 0.48, 0.02]) #colorbar axes
        cb = colorbar(cax=cax, orientation='horizontal')
        cb.set_label(Label)

        # pdb.set_trace()
        # Save figure into a local directory called figures. Make directory if it doesn't exist.
        if not os.path.exists('figures'):
            os.makedirs('figures')

        savefig('figures/' + fname + 'histhexbin.png', bbox_inches='tight')
        # savefig('figures/' + fname + 'histhexbin.pdf',bbox_inches='tight')

    elif which == 'hist2d':
        # pdb.set_trace()

        hist2d(xpc, ypc, bins=40, 
                range=[[grid['xr'].min(), grid['xr'].max()], 
                [grid['yr'].min(), grid['yr'].max()]], normed=True)
        set_cmap('YlOrRd')
        # Set x and y limits
        # pdb.set_trace()
        if xlims is not None:
            xlim(xlims)
        if ylims is not None:
            ylim(ylims)

        # Horizontal colorbar below plot
        cax = fig.add_axes([0.3775, 0.25, 0.48, 0.02]) #colorbar axes
        cb = colorbar(cax=cax,orientation='horizontal')
        cb.set_label('Final drifter location (percent)')

        # Save figure into a local directory called figures. Make directory if it doesn't exist.
        if not os.path.exists('figures'):
            os.makedirs('figures')

        savefig('figures/' + fname + 'hist2d.png',bbox_inches='tight')
        # savefig('figures/' + fname + 'histpcolor.pdf',bbox_inches='tight')


def tracks(lonp,latp,fname,grid=None, fig=None, ax=None, Title=None, mers=None, pars=None, isll=True):
    """
    Plot tracks as lines with starting points in green and ending points in red.

    Inputs:
        lonp,latp   Drifter track positions [time x ndrifters]
        fname       Plot name to save
    """
    # pdb.set_trace()
    if grid is None:
        loc = 'http://barataria.tamu.edu:8080/thredds/dodsC/NcML/txla_nesting6.nc'
        grid = inout.readgrid(loc)

    if fig is None:
        figure(figsize=(12,10))
    else:
        fig = fig

    if ax is None:
        ax = gca()
    else:
        ax = ax

    if isll:
        # Change positions from lon/lat to x/y
        xp,yp = grid['basemap'](lonp,latp)
        # Need to retain nan's since basemap changes them to values
        ind = np.isnan(lonp)
        xp[ind] = np.nan
        yp[ind] = np.nan
    else:
        xp = lonp;
        yp = latp;
  
    if mers is not None:
        background(grid, ax=ax, mers=mers, pars=pars) # Plot coastline and such
    else:
        background(grid, ax=ax) # Plot coastline and such
    # pdb.set_trace()

    # Starting marker
    ax.plot(xp[:,0],yp[:,0],'o',color='g',markersize=3,label='_nolegend_',alpha=0.4)

    # Plot tracks
    ax.plot(xp.T,yp.T,'-',color='grey',linewidth=.2)

    # Find final positions of drifters
    xpc,ypc = tools.find_final(xp,yp)
    ax.plot(xpc,ypc,'o', alpha=0.8, color='#e34a33',label='_nolegend_')
    # pdb.set_trace()

    if Title is not None:
        ax.set_title(Title)

    # Legend, of sorts
    # ax = gca()
    xtext = 0.45; ytext = 0.18;
    text(xtext, ytext, 'starting location', fontsize=16, color='green', 
        alpha=.8, transform = ax.transAxes)
    text(xtext, ytext-.03, 'track', fontsize=16, color='grey', transform = ax.transAxes)
    text(xtext, ytext-.03*2, 'ending location', fontsize=16, color='red', 
        transform = ax.transAxes)
    # xtext, ytext = grid['basemap'](-94,24) # text location
    # text(xtext,ytext,'starting location',fontsize=16,color='green',alpha=.8)
    # text(xtext,ytext-30000,'track',fontsize=16,color='grey')#,alpha=.8)
    # text(xtext,ytext-60000,'ending location',fontsize=16,color='red')#,alpha=.8)

    # # get psi mask from rho mask
    # # maskp = grid['mask'][1:,1:]*grid['mask'][:-1,1:]* \
 # #               grid['mask'][1:,:-1]*grid['mask'][:-1,:-1] 
    # # ind = maskp
    # # ind[ind==0] = np.nan
    # # plot(grid['xpsi']*ind,grid['ypsi']*ind,'k', \
    # #         (grid['xpsi']*ind).T,(grid['ypsi']*ind).T,'k')
    # plot(grid['xpsi'],grid['ypsi'],'k', \
    #       (grid['xpsi']).T,(grid['ypsi']).T,'k')

    # 16 is (lower) one that is near islands, 41 is higher one

    # show()

    # Save figure into a local directory called figures. Make directory if it doesn't exist.
    if not os.path.exists('figures'):
        os.makedirs('figures')

    savefig('figures/' + fname + 'tracks.png',bbox_inches='tight')
    # savefig('figures/' + fname + 'tracks.pdf',bbox_inches='tight')

def transport(name, fmod=None, Title=None, dmax=None, N=7, extraname=None,
                llcrnrlon=-98.5, llcrnrlat=22.5, urcrnrlat=31.0, urcrnrlon=-87.5,
                colormap='Blues',fig=None, ax=None):
    '''
    Make plot of zoomed-in area near DWH spill of transport of drifters over 
    time.

    FILL IN

    Inputs:
        name
        U
        V
        lon0
        lat0
        T0
    '''


# (name=None, U, V, lon0, lat0, T0, dmax, extraname, Title, N,
                # llcrnrlon, llcrnrlat, urcrnrlat, urcrnrlon, colormap):

    # Load in transport information
    U, V, lon0, lat0, T0 = inout.loadtransport(name,fmod=fmod)

    # Smaller basemap parameters.
    loc = 'http://barataria.tamu.edu:8080/thredds/dodsC/NcML/txla_nesting6.nc'
    grid = inout.readgrid(loc, llcrnrlon=llcrnrlon, llcrnrlat=llcrnrlat, 
                                    urcrnrlat=urcrnrlat, urcrnrlon=urcrnrlon)

    S = np.sqrt(op.resize(U,1)**2+op.resize(V,0)**2)
    Splot = (S/T0)*100
    if dmax is None:
        dmax = Splot.max()
    else:
        dmax = dmax
    # from http://matplotlib.1069221.n5.nabble.com/question-about-contours-and-clim-td21111.html
    locator = ticker.MaxNLocator(N) # if you want no more than 10 contours
    locator.create_dummy_axis()
    locator.set_bounds(0,dmax)#d.min(),d.max())
    levs = locator()

    if fig is None:
        fig = figure(figsize=(11,10))
    else:
        fig = fig
    background(grid=grid)
    c = contourf(grid['xpsi'], grid['ypsi'], Splot,             
            cmap=colormap, extend='max', levels=levs)
    title(Title)

    # # Add initial drifter location (all drifters start at the same location)
    # lon0 = lon0.mean()
    # lat0 = lat0.mean()
    # x0, y0 = grid['basemap'](lon0, lat0)
    # plot(x0, y0, 'go', markersize=10)

    if ax is None:
        ax = gca()
    else:
        ax = ax
    # Want colorbar at the given location relative to axis so this works regardless of # of subplots, 
    # so convert from axis to figure coordinates
    # To do this, first convert from axis to display coords
    # transformations: http://matplotlib.org/users/transforms_tutorial.html
    ax_coords = [0.35, 0.25, 0.6, 0.02] # axis: [x_left, y_bottom, width, height]
    disp_coords = ax.transAxes.transform([(ax_coords[0],ax_coords[1]),(ax_coords[0]+ax_coords[2],ax_coords[1]+ax_coords[3])]) # display: [x_left,y_bottom,x_right,y_top]
    inv = fig.transFigure.inverted() # inverter object to go from display coords to figure coords
    fig_coords = inv.transform(disp_coords) # figure: [x_left,y_bottom,x_right,y_top]
    # actual desired figure coords. figure: [x_left, y_bottom, width, height]
    fig_coords = [fig_coords[0,0],fig_coords[0,1],fig_coords[1,0]-fig_coords[0,0],fig_coords[1,1]-fig_coords[0,1]]
    # Inlaid colorbar
    cax = fig.add_axes(fig_coords)
    # cax = fig.add_axes([0.39, 0.25, 0.49, 0.02])
    # cax = fig.add_axes([0.49, 0.25, 0.39, 0.02])
    cb = colorbar(cax=cax,orientation='horizontal')
    cb.set_label('Normalized drifter transport (%)')

    if extraname is None:
        savefig('figures/' + name + '/transport', bbox_inches='tight')
    else:
        savefig('figures/' + name + '/' + extraname + 'transport', bbox_inches='tight')

import numpy as np
import xarray as xr
import uxarray as ux
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.animation as animation
import matplotlib as mpl
import numpy as np
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geoviews.feature as gf
from cartopy.crs import PlateCarree
from matplotlib.colors import LinearSegmentedColormap, PowerNorm
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from geocat.comp.interpolation import interp_hybrid_to_pressure

def SubsetLatLon(ux_dataset, var_string, xlims, ylims):
    return ux_dataset[var_string].subset.bounding_box(lon_bounds=xlims, lat_bounds=ylims)

def ListedCMAP_Wrapper(color_cutoff_bounds, base_cmap_name):
    base_cmap = mpl.colormaps[base_cmap_name]

    N = len(color_cutoff_bounds)
    norm = mpl.colors.BoundaryNorm(color_cutoff_bounds, N)
    x = np.linspace(0, 1, N)

    # Linear
    lin_cm = mpl.colors.ListedColormap(base_cmap(x**1.0))

    # Low
    low_cm = mpl.colors.ListedColormap(base_cmap(x**0.5))

    # High
    high_cm = mpl.colors.ListedColormap(base_cmap(x**2.0))

    fig = plt.figure(layout='constrained')
    for i, (cmap, title) in enumerate([(lin_cm, 'linear'), (low_cm, 'low'), (high_cm, 'high')]):
        ax = fig.add_subplot(1, 3, i+1)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax,
                     ticks=color_cutoff_bounds)
        ax.set_title(title)

    return norm, lin_cm, low_cm, high_cm

def Hybrid2plev(ux_dataset, var_string, xlims, ylims, destination_plevs_pascals, interp_method_str, return_as_ux):

    # hybrid coefficients
    hyam = ux_dataset.hyam
    hybm = ux_dataset.hybm

    subsetted_var = SubsetLatLon(ux_dataset, var_string, xlims, ylims)
    subsetted_PS = SubsetLatLon(ux_dataset, "PS", xlims, ylims)

    subset_on_isobars_da = interp_hybrid_to_pressure(subsetted_var,
                                                     subsetted_PS,
                                                     hyam,
                                                     hybm,
                                                     new_levels=destination_plevs_pascals,
                                                     method=interp_method_str)

    if (return_as_ux):
        return ux.UxDataArray.from_xarray(subset_on_isobars_da, subsetted_var.uxgrid)
    else:
        return subset_on_isobars_da

def PlotHelper(subsetted_2D_var,
               title_no_end_space,
               microp_status,
               anim_save_path,
               xlims,
               ylims,
               a_cmap,
               bounds,
               color_norm,
               cb_label,
               projection=ccrs.PlateCarree(),
               figsize=(8, 6),
               dpi=200):

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi, subplot_kw={"projection": projection})

    ax.set_extent((xlims[0], xlims[1], ylims[0], ylims[1]), crs=projection)
    ax.set_xticks(range(xlims[0], xlims[1]+1), crs=projection)
    ax.set_yticks(range(ylims[0], ylims[1]+1), crs=projection)
    ax.add_feature(cfeature.STATES)

    raster_temp = subsetted_2D_var[0, :].to_raster(ax=ax)

    im = ax.imshow(
        raster_temp,
        cmap=a_cmap,
        origin="lower",
        norm=color_norm,
        extent=ax.get_xlim() + ax.get_ylim()
    )

    # Add an Axes to the right of the main Axes.
    ax_divider = make_axes_locatable(ax)
    cax = ax_divider.append_axes("right", size="7%", pad="2%", axes_class=plt.Axes)
    cb = fig.colorbar(im, cax=cax, ticks=bounds, extend='both')
    cb.set_label(cb_label)
    cb.ax.tick_params(labelsize=8)

    fig.canvas.draw()

    print('Getting pixel mapping...')
    raster_0, pixel_mapping = subsetted_2D_var[0, :].to_raster(ax=ax,
                                                               return_pixel_mapping=True)
    print('Done with pixel mapping!')

    # ---------------------------------------------------------------
    # Animation
    # ---------------------------------------------------------------
    def update(frame):
        print(f'frame {frame}')
        im.set_data(subsetted_2D_var[frame, :].to_raster(ax=ax, pixel_mapping=pixel_mapping))
        ax.set_title(f'{title_no_end_space} {subsetted_2D_var[frame, :].time.values.item().strftime("%H:%M")}\nmicrop_uniform={microp_status}')
        return im

    ani = animation.FuncAnimation(fig, update, frames=range(48))

    print(f'Saving animation to {anim_save_path}')
    ani.save(anim_save_path)
    print('Animation saved!')

def ContourPlotHelper(subsetted_2D_var,
               title_no_end_space,
               microp_status,
               anim_save_path,
               xlims,
               ylims,
               bounds,
               projection=ccrs.PlateCarree(),
               figsize=(8, 6),
               dpi=200):

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi, subplot_kw={"projection": projection})

    ax.set_extent((xlims[0], xlims[1], ylims[0], ylims[1]), crs=projection)
    ax.set_xticks(range(xlims[0], xlims[1]+1), crs=projection)
    ax.set_yticks(range(ylims[0], ylims[1]+1), crs=projection)
    ax.add_feature(cfeature.STATES)

    raster_temp = subsetted_2D_var[0, :].to_raster(ax=ax)

    contour = ax.contour(raster_temp,
                         colors='black',
                         origin='lower',
                         extent=ax.get_xlim() + ax.get_ylim(),
                         levels=bounds
                        )

    fig.canvas.draw()

    print('Getting pixel mapping...')
    raster_0, pixel_mapping = subsetted_2D_var[0, :].to_raster(ax=ax,
                                                               return_pixel_mapping=True)
    print('Done with pixel mapping!')

    # ---------------------------------------------------------------
    # Animation
    # ---------------------------------------------------------------
    def update(frame):
        nonlocal contour
        print(f'frame {frame}')

        contour.remove()

        contour = ax.contour(subsetted_2D_var[frame, :].to_raster(ax=ax, pixel_mapping=pixel_mapping),
                             colors='black',
                             origin='lower',
                             extent=ax.get_xlim() + ax.get_ylim(),
                             levels=bounds
                            )
        ax.clabel(contour, contour.levels)
        ax.set_title(f'{title_no_end_space} {subsetted_2D_var[frame, :].time.values.item().strftime("%H:%M")}\nmicrop_uniform={microp_status}')
        return contour

    ani = animation.FuncAnimation(fig, update, frames=range(48))

    print(f'Saving animation to {anim_save_path}')
    ani.save(anim_save_path)
    print('Animation saved!')
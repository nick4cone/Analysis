import uxarray as ux
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime


def global_plot(exodus_path, save_path):
    uxgrid = ux.open_grid(exodus_path)
    print('uxgrid.dims: ', uxgrid.dims)
    print('uxgrid.sizes: ', uxgrid.sizes)
    print('uxgrid.coordinates: ', uxgrid.coordinates)
    lc = uxgrid.to_linecollection(colors="black", linewidths=0.5)
    fig, ax = plt.subplots(
        1,
        1,
        figsize=(10, 10),
        constrained_layout=True,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_collection(lc)
    ax.set_global()
    ax.set_title("LineCollection Plot")
    now = datetime.now()
    date_string = now.strftime('_%m-%d-%Y_%H-%M-%S')
    plt.savefig(save_path+date_string)

"""
Raster tools

You can use this only if you have installed sertit[full] or sertit[rasters]
"""
import os
from functools import wraps
from typing import Union, Optional, Any, Callable
import numpy as np
import xarray

from sertit.rasters_rio import path_arr_dst, PATH_ARR_DS

try:
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Polygon

    import rasterio
    from rasterio import features

    import xarray as xr
    import rioxarray
    from rioxarray import merge
    from rasterio.enums import Resampling
except ModuleNotFoundError as ex:
    raise ModuleNotFoundError("Please install 'rioxarray' and 'geopandas' to use the 'rasters' package.") from ex

from sertit import vectors, rasters_rio, files

MAX_CORES = os.cpu_count() - 2
ORIGIN_DTYPE = 'original_dtype'
PATH_XARR_DS = Union[str, xr.DataArray, xr.Dataset, rasterio.DatasetReader]
"""
Types: 

- Path
- rasterio Dataset
- `xarray.DataArray` and `xarray.Dataset`
"""

XDS_TYPE = Union[xr.Dataset, xr.DataArray]
"""
Xarray types: xr.Dataset and xr.DataArray
"""


def path_xarr_dst(function: Callable) -> Callable:
    """
    Path, `xarray` or dataset decorator. Allows a function to ingest:

    - a path
    - a `xarray`
    - a `rasterio` dataset

    ```python
    >>> # Create mock function
    >>> @path_or_dst
    >>> def fct(dst):
    >>>     read(dst)
    >>>
    >>> # Test the two ways
    >>> read1 = fct("path\\to\\raster.tif")
    >>> with rasterio.open("path\\to\\raster.tif") as dst:
    >>>     read2 = fct(dst)
    >>>
    >>> # Test
    >>> read1 == read2
    True
    ```
    Args:
        function (Callable): Function to decorate

    Returns:
        Callable: decorated function
    """

    @wraps(function)
    def path_or_xarr_or_dst_wrapper(path_or_ds: PATH_XARR_DS, *args, **kwargs) -> Any:
        """
        Path or dataset wrapper
        Args:
            path_or_ds (PATH_XARR_DS): Raster path or its dataset
            *args: args
            **kwargs: kwargs

        Returns:
            Any: regular output
        """
        if isinstance(path_or_ds, (xr.DataArray)):
            out = function(path_or_ds, *args, **kwargs)
        elif isinstance(path_or_ds, (xr.Dataset)):
            # Try on the whole dataset
            try:
                out = function(path_or_ds, *args, **kwargs)
            except Exception:
                # Try on every dataarray
                try:
                    xds_dict = {}
                    convert_to_xdataset = False
                    for var in path_or_ds.data_vars:
                        xds_dict[var] = function(path_or_ds[var], *args, **kwargs)
                        if isinstance(xds_dict[var], xr.DataArray):
                            convert_to_xdataset = True

                    # Convert in dataset if we have dataarrays, else keep the dict
                    if convert_to_xdataset:
                        xds = xr.Dataset(xds_dict)
                    else:
                        xds = xds_dict
                    return xds
                except Exception as ex:
                    raise TypeError("Function not available for xarray.Dataset") from ex
        else:
            # Get name
            if isinstance(path_or_ds, str):
                name = path_or_ds
            else:
                name = path_or_ds.name

            with rioxarray.open_rasterio(path_or_ds, masked=True, default_name=name) as xds:
                xds.attrs[ORIGIN_DTYPE] = rioxarray.open_rasterio(path_or_ds).dtype  # TODO
                out = function(xds, *args, **kwargs)
        return out

    return path_or_xarr_or_dst_wrapper


def _get_nodata_pos(xds: XDS_TYPE) -> np.ndarray:
    """
    Get nodata positions in the xarray as a `np.ndarray` with `True` where nodata values are.

    Args:
        xds (XDS_TYPE): Xarray

    Returns:
        np.ndarray: Boolean array with True w

    """
    nodata = xds.rio.nodata

    try:
        is_nan = np.isnan(nodata)
    except TypeError:
        is_nan = False

    if is_nan:
        nodata_pos = np.isnan(xds.data)
    else:
        nodata_pos = xds.data == nodata

    return nodata_pos


def to_np(xds: xarray.DataArray, dtype: str = None) -> np.ndarray:
    """
    Convert the `xarray` to a `np.ndarray` with the correct nodata encoded.

    This is particularly useful when reading with `masked=True`.

    ```python
    >>> raster_path = "path\\to\\mask.tif"  # Classified raster in np.uint8 with nodata = 255
    >>> # We read with masked=True so the data is converted to float
    >>> xds = read(raster_path)
    <xarray.DataArray 'path/to/mask.tif' (band: 1, y: 322, x: 464)>
    [149408 values with dtype=float64]
    Coordinates:
      * band         (band) int32 1
      * y            (y) float64 4.798e+06 4.798e+06 ... 4.788e+06 4.788e+06
      * x            (x) float64 5.411e+05 5.411e+05 ... 5.549e+05 5.55e+05
        spatial_ref  int32 0
    >>> to_np(xds)  # Getting back np.uint8 and encoded nodata
    array([[[255, 255, 255, ..., 255, 255, 255],
        [255, 255, 255, ..., 255, 255, 255],
        [255, 255, 255, ..., 255, 255, 255],
        ...,
        [255, 255, 255, ...,   1, 255, 255],
        [255, 255, 255, ...,   1, 255, 255],
        [255, 255, 255, ...,   1, 255, 255]]], dtype=uint8)

    True
    ```
    Args:
        xds (xarray.DataArray): `xarray.DataArray` to convert
        dtype (str): Dtype to convert to. If None, using the origin dtype if existing or its current dtype.

    Returns:

    """
    if not dtype:
        dtype = xds.attrs.get(ORIGIN_DTYPE, xds.dtype)
    arr = np.where(_get_nodata_pos(xds), xds.rio.encoded_nodata, xds.data).astype(dtype)

    return arr


def get_nodata_mask(xds: XDS_TYPE) -> np.ndarray:
    """
    Get nodata mask from a xarray.

    ```python
    >>> diag_arr = xr.DataArray(data=np.diag([1, 2, 3]))
    >>> diag_arr.rio.write_nodata(0, inplace=True)
    <xarray.DataArray (dim_0: 3, dim_1: 3)>
    array([[1, 0, 0],
           [0, 2, 0],
           [0, 0, 3]])
    Dimensions without coordinates: dim_0, dim_1
    Attributes: _FillValue:  0

    >>> get_nodata_mask(diag_arr)
    array([[1, 0, 0],
           [0, 1, 0],
           [0, 0, 1]], dtype=uint8)
    ```

    Args:
        xds (XDS_TYPE): Array to evaluate

    Returns:
        np.ndarray: Pixelwise nodata array

    """
    return np.where(_get_nodata_pos(xds), 0, 1).astype(np.uint8)


@path_xarr_dst
def _vectorize(xds: PATH_XARR_DS,
               values: Union[None, int, list] = None,
               get_nodata: bool = False,
               default_nodata: int = 0) -> gpd.GeoDataFrame:
    """
    Vectorize a xarray, both to get classes or nodata.

    .. WARNING::
        - If `get_nodata` is set to False:
            - Your data is casted by force into np.uint8, so be sure that your data is classified.
            - This could take a while as the computing time directly depends on the number of polygons to vectorize.
                Please be careful.
    Else:
        - You will get a classified polygon with data (value=0)/nodata pixels. To

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray
        values (Union[None, int, list]): Get only the polygons concerning this/these particular values
        get_nodata (bool): Get nodata vector (raster values are set to 0, nodata values are the other ones)
        default_nodata (int): Default values for nodata in case of non existing in file
    Returns:
        gpd.GeoDataFrame: Vector
    """
    # Manage nodata value
    has_nodata = xds.rio.encoded_nodata is not None
    nodata = xds.rio.encoded_nodata if has_nodata else default_nodata

    if get_nodata:
        data = get_nodata_mask(xds)
        nodata_arr = None
    else:
        data = to_np(xds)
        # Manage values
        if values is not None:
            if not isinstance(values, list):
                values = [values]
            data = np.where(np.isin(data, values), data, nodata).astype(np.uint8)

        if data.dtype != np.uint8:
            raise TypeError("Your data should be classified (np.uint8).")

        nodata_arr = rasters_rio.get_nodata_mask(data, has_nodata=False, default_nodata=nodata)

    # Get shapes (on array or on mask to get nodata vector)
    shapes = features.shapes(data, mask=nodata_arr, transform=xds.rio.transform())

    return vectors.shapes_to_gdf(shapes, xds.rio.crs)


@path_xarr_dst
def vectorize(xds: PATH_XARR_DS,
              values: Union[None, int, list] = None,
              default_nodata: int = 0) -> gpd.GeoDataFrame:
    """
    Vectorize a `xarray` to get the class vectors.


    .. WARNING::
        - Your data is casted by force into np.uint8, so be sure that your data is classified.
        - This could take a while as the computing time directly depends on the number of polygons to vectorize.
            Please be careful.

    ```python
    >>> raster_path = "path\\to\\raster.tif"
    >>> vec1 = vectorize(raster_path)
    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>     vec2 = vectorize(dst)
    >>> vec1 == vec2
    True
    ```

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray
        values (Union[None, int, list]): Get only the polygons concerning this/these particular values
        default_nodata (int): Default values for nodata in case of non existing in file
    Returns:
        gpd.GeoDataFrame: Classes Vector
    """
    return _vectorize(xds, values=values, get_nodata=False, default_nodata=default_nodata)


@path_xarr_dst
def get_valid_vector(xds: PATH_XARR_DS,
                     default_nodata: int = 0) -> gpd.GeoDataFrame:
    """
    Get the valid data of a raster as a vector.

    Pay attention that every nodata pixel will appear too.
    If you want only the footprint of the raster, please use `get_footprint`.

    ```python
    >>> raster_path = "path\\to\\raster.tif"
    >>> nodata1 = get_nodata_vec(raster_path)
    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>     nodata2 = get_nodata_vec(dst)
    >>> nodata1 == nodata2
    True
    ```

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray
        default_nodata (int): Default values for nodata in case of non existing in file
    Returns:
        gpd.GeoDataFrame: Nodata Vector

    """
    nodata = _vectorize(xds, values=None, get_nodata=True, default_nodata=default_nodata)
    return nodata[nodata.raster_val != 0]  # 0 is the values of not nodata put there by rasterio


@path_xarr_dst
def get_nodata_vector(dst: PATH_ARR_DS,
                      default_nodata: int = 0) -> gpd.GeoDataFrame:
    """
    Get the nodata vector of a raster as a vector.

    Pay attention that every nodata pixel will appear too.
    If you want only the footprint of the raster, please use `get_footprint`.

    ```python
    >>> raster_path = "path\\to\\raster.tif"  # Classified raster, with no data set to 255
    >>> nodata1 = get_nodata_vec(raster_path)
    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>     nodata2 = get_nodata_vec(dst)
    >>> nodata1 == nodata2
    True
    ```

    Args:
        dst (PATH_ARR_DS): Path to the raster, its dataset, its `xarray` or a tuple containing its array and metadata
        default_nodata (int): Default values for nodata in case of non existing in file
    Returns:
        gpd.GeoDataFrame: Nodata Vector

    """
    nodata = _vectorize(dst, values=None, get_nodata=True, default_nodata=default_nodata)
    return nodata[nodata.raster_val == 0]


@path_xarr_dst
def mask(xds: PATH_XARR_DS,
         shapes: Union[Polygon, list],
         nodata: Optional[int] = None,
         **kwargs) -> XDS_TYPE:
    """
    Masking a dataset:
    setting nodata outside of the given shapes, but without cropping the raster to the shapes extent.

    Overload of rasterio mask function in order to create a masked_array.

    The `mask` function doc can be seen [here](https://rasterio.readthedocs.io/en/latest/api/rasterio.mask.html).
    It basically masks a raster with a vector mask, with the possibility to crop the raster to the vector's extent.

    ```python
    >>> raster_path = "path\\to\\raster.tif"
    >>> shape_path = "path\\to\\shapes.geojson"  # Any vector that geopandas can read
    >>> shapes = gpd.read_file(shape_path)
    >>> masked_raster1, meta1 = mask(raster_path, shapes)
    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>     masked_raster2, meta2 = mask(dst, shapes)
    >>> masked_raster1 == masked_raster2
    True
    >>> meta1 == meta2
    True
    ```

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray
        shapes (Union[Polygon, list]): Shapes
        nodata (int): Nodata value. If not set, uses the ds.nodata. If doesnt exist, set to 0.
        **kwargs: Other rasterio.mask options

    Returns:
         (np.ma.masked_array, dict): Masked array as a masked array and its metadata
    """
    # Use classic option
    arr, _ = rasters_rio.mask(xds, shapes=shapes, nodata=nodata, **kwargs)

    # Convert back to xarray
    return xds.copy(data=arr, deep=True)


@path_xarr_dst
def crop(xds: PATH_XARR_DS,
         shapes: Union[Polygon, list],
         nodata: Optional[int] = None,
         **kwargs) -> (np.ma.masked_array, dict):
    """
    Cropping a dataset:
    setting nodata outside of the given shapes AND cropping the raster to the shapes extent.

    Overload of [`rioxarray`
    clip](https://corteva.github.io/rioxarray/stable/rioxarray.html#rioxarray.raster_array.RasterArray.clip)
    function in order to create a masked_array.

    ```python
    >>> raster_path = "path\\to\\raster.tif"
    >>> shape_path = "path\\to\\shapes.geojson"  # Any vector that geopandas can read
    >>> shapes = gpd.read_file(shape_path)
    >>> xds2 = crop(raster_path, shapes)
    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>     xds2 = crop(dst, shapes)
    >>> xds1 == xds2
    True
    ```

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray
        shapes (Union[Polygon, list]): Shapes
        nodata (int): Nodata value. If not set, uses the ds.nodata. If doesnt exist, set to 0.
        **kwargs: Other rioxarray.clip options

    Returns:
         XDS_TYPE: Cropped array as a xarray
    """
    if nodata:
        xds_new = xds.rio.write_nodata(nodata)
    else:
        xds_new = xds

    return xds_new.rio.clip(shapes, **kwargs)  # Keep consistency with rasterio


@path_arr_dst
def read(dst: PATH_ARR_DS,
         resolution: Union[tuple, list, float] = None,
         size: Union[tuple, list] = None,
         resampling: Resampling = Resampling.nearest,
         masked: bool = True) -> XDS_TYPE:
    """
    Read a raster dataset from a :

    - `xarray` (compatibility issues)
    - `rasterio.Dataset`
    - `rasterio` opened data (array, metadata)
    - a path.

    The resolution can be provided (in dataset unit) as:

    - a tuple or a list of (X, Y) resolutions
    - a float, in which case X resolution = Y resolution
    - None, in which case the dataset resolution will be used

    ```python
    >>> raster_path = "path\\to\\raster.tif"
    >>> xds1 = read(raster_path)
    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>    xds2 = read(dst)
    >>> xds1 == xds2
    True
    ```

    Args:
        dst (PATH_ARR_DS): Path to the raster or a rasterio dataset or a xarray
        resolution (Union[tuple, list, float]): Resolution of the wanted band, in dataset resolution unit (X, Y)
        size (Union[tuple, list]): Size of the array (width, height). Not used if resolution is provided.
        resampling (Resampling): Resampling method
        masked (bool): Get a masked array

    Returns:
        Union[XDS_TYPE]: Masked xarray corresponding to the raster data and its meta data

    """
    # Get new height and width
    new_height, new_width = rasters_rio.get_new_shape(dst, resolution, size)

    # Read data
    xds = rioxarray.open_rasterio(dst, mask_and_scale=masked, default_name=files.get_filename(dst.name))
    if masked:
        xds.attrs[ORIGIN_DTYPE] = rioxarray.open_rasterio(dst).dtype  # TODO
    else:
        xds.attrs[ORIGIN_DTYPE] = xds.dtype

    if new_height != dst.height or new_width != dst.width:
        xds = xds.rio.reproject(xds.rio.crs, shape=(new_height, new_width), resampling=resampling)

    return xds


@path_xarr_dst
def write(xds: XDS_TYPE,
          path: str,
          **kwargs) -> None:
    """
    Write raster to disk.
    (encapsulation of `rasterio`'s function, because for now `rioxarray` to_raster doesn't work as expected)

    Metadata will be created with the `xarray` metadata (ie. width, height, count, type...)
    The driver is `GTiff` by default, and no nodata value is provided.
    The file will be compressed if the raster is a mask (saved as uint8).

    ```python
    >>> raster_path = "path\\to\\raster.tif"
    >>> raster_out = "path\\to\\out.tif"

    >>> # Read raster
    >>> xds = read(raster_path)

    >>> # Rewrite it
    >>> write(xds, raster_out)
    ```

    Args:
        xds (XDS_TYPE): Path to the raster or a rasterio dataset or a xarray
        path (str): Path where to save it (directories should be existing)
        **kwargs: Overloading metadata, ie `nodata=255`
    """
    xds.rio.to_raster(path, **kwargs)


def collocate(master_xds: XDS_TYPE,
              slave_xds: XDS_TYPE,
              resampling: Resampling = Resampling.nearest) -> XDS_TYPE:
    """
    Collocate two georeferenced arrays:
    forces the *slave* raster to be exactly georeferenced onto the *master* raster by reprojection.

    Use it like `OTB SuperImpose`.

    ```python
    >>> master_path = "path\\to\\master.tif"
    >>> slave_path = "path\\to\\slave.tif"
    >>> col_path = "path\\to\\collocated.tif"

    >>> # Collocate the slave to the master
    >>> col_xds = collocate(read(master_path), read(slave_path), Resampling.bilinear)

    >>> # Write it
    >>> write(col_xds, col_path)
    ```

    Args:
        master_xds (XDS_TYPE): Master xarray
        slave_xds (XDS_TYPE): Slave xarray
        resampling (Resampling): Resampling method

    Returns:
        XDS_TYPE: Collocated xarray

    """
    collocated_xds = slave_xds.rio.reproject_match(master_xds, resampling=resampling)
    collocated_xds = collocated_xds.assign_coords({
        "x": master_xds.x,
        "y": master_xds.y,
    })  # Bug for now, tiny difference in coords
    return collocated_xds


@path_xarr_dst
def sieve(xds: PATH_XARR_DS,
          sieve_thresh: int,
          connectivity: int = 4) -> XDS_TYPE:
    """
    Sieving, overloads rasterio function with raster shaped like (1, h, w).

    .. WARNING::
        Your data is casted by force into `np.uint8`, so be sure that your data is classified.

    ```python
    >>> raster_path = "path\\to\\raster.tif"  # classified raster

    >>> # Rewrite it
    >>> sieved_xds = sieve(raster_path, sieve_thresh=20)

    >>> # Write it
    >>> raster_out = "path\\to\\raster_sieved.tif"
    >>> write(sieved_xds, raster_out)
    ```

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray
        sieve_thresh (int): Sieving threshold in pixels
        connectivity (int): Connectivity, either 4 or 8

    Returns:
        (XDS_TYPE): Sieved xarray
    """
    assert connectivity in [4, 8]

    # Sieve
    data = np.squeeze(to_np(xds))  # Use this trick to make the sieve work
    sieved_data = features.sieve(data, size=sieve_thresh, connectivity=connectivity)
    sieved_xds = xds.copy(data=np.expand_dims(sieved_data.astype(xds.dtype), axis=0), deep=True)

    return sieved_xds


def get_dim_img_path(dim_path: str, img_name: str = '*') -> str:
    """
    Get the image path from a *BEAM-DIMAP* data.

    A *BEAM-DIMAP* file cannot be opened by rasterio, although its .img file can.

    ```python
    >>> dim_path = "path\\to\\dimap.dim"  # BEAM-DIMAP image
    >>> img_path = get_dim_img_path(dim_path)

    >>> # Read raster
    >>> raster, meta = read(img_path)
    ```

    Args:
        dim_path (str): DIM path (.dim or .data)
        img_name (str): .img file name (or regex), in case there are multiple .img files (ie. for S3 data)

    Returns:
        str: .img file
    """
    return rasters_rio.get_dim_img_path(dim_path, img_name)


@path_xarr_dst
def get_extent(xds: PATH_XARR_DS) -> gpd.GeoDataFrame:
    """
    Get the extent of a raster as a `geopandas.Geodataframe`.

    ```python
    >>> raster_path = "path\\to\\raster.tif"

    >>> extent1 = get_extent(raster_path)
    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>     extent2 = get_extent(dst)
    >>> extent1 == extent2
    True
    ```

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray

    Returns:
        gpd.GeoDataFrame: Extent as a `geopandas.Geodataframe`
    """
    return vectors.get_geodf(geometry=[*xds.rio.bounds()], crs=xds.rio.crs)


@path_xarr_dst
def get_footprint(xds: PATH_XARR_DS) -> gpd.GeoDataFrame:
    """
    Get real footprint of the product (without nodata, in french == emprise utile)

    ```python
    >>> raster_path = "path\\to\\raster.tif"

    >>> footprint1 = get_footprint(raster_path)

    >>> # or
    >>> with rasterio.open(raster_path) as dst:
    >>>     footprint2 = get_footprint(dst)
    >>> footprint1 == footprint2
    ```

    Args:
        xds (PATH_XARR_DS): Path to the raster or a rasterio dataset or a xarray
    Returns:
        gpd.GeoDataFrame: Footprint as a GeoDataFrame
    """
    footprint = get_valid_vector(xds)
    return vectors.get_wider_exterior(footprint)


def merge_vrt(crs_paths: list, crs_merged_path: str, **kwargs) -> None:
    """
    Merge rasters as a VRT. Uses `gdalbuildvrt`.

    See here: https://gdal.org/programs/gdalbuildvrt.html

    Creates VRT with relative paths !

    .. WARNING::
        They should have the same CRS otherwise the mosaic will be false !

    ```python
    >>> paths_utm32630 = ["path\\to\\raster1.tif", "path\\to\\raster2.tif", "path\\to\\raster3.tif"]
    >>> paths_utm32631 = ["path\\to\\raster4.tif", "path\\to\\raster5.tif"]

    >>> mosaic_32630 = "path\\to\\mosaic_32630.vrt"
    >>> mosaic_32631 = "path\\to\\mosaic_32631.vrt"

    >>> # Create mosaic, one by CRS !
    >>> merge_vrt(paths_utm32630, mosaic_32630)
    >>> merge_vrt(paths_utm32631, mosaic_32631, {"-srcnodata":255, "-vrtnodata":0})
    ```

    Args:
        crs_paths (list): Path of the rasters to be merged with the same CRS)
        crs_merged_path (str): Path to the merged raster
        kwargs: Other gdlabuildvrt arguments
    """
    return rasters_rio.merge_vrt(crs_paths, crs_merged_path, **kwargs)


def merge_gtiff(crs_paths: list, crs_merged_path: str, **kwargs) -> None:
    """
    Merge rasters as a GeoTiff.

    .. WARNING::
        They should have the same CRS otherwise the mosaic will be false !

    ```python
    >>> paths_utm32630 = ["path\\to\\raster1.tif", "path\\to\\raster2.tif", "path\\to\\raster3.tif"]
    >>> paths_utm32631 = ["path\\to\\raster4.tif", "path\\to\\raster5.tif"]

    >>> mosaic_32630 = "path\\to\\mosaic_32630.tif"
    >>> mosaic_32631 = "path\\to\\mosaic_32631.tif"

    # Create mosaic, one by CRS !
    >>> merge_gtiff(paths_utm32630, mosaic_32630)
    >>> merge_gtiff(paths_utm32631, mosaic_32631)
    ```

    Args:
        crs_paths (list): Path of the rasters to be merged with the same CRS)
        crs_merged_path (str): Path to the merged raster
        kwargs: Other rasterio.merge arguments
            More info [here](https://rasterio.readthedocs.io/en/latest/api/rasterio.merge.html#rasterio.merge.merge)
    """
    return rasters_rio.merge_gtiff(crs_paths, crs_merged_path, **kwargs)


def unpackbits(array: np.ndarray, nof_bits: int) -> np.ndarray:
    """
    Function found here:
    https://stackoverflow.com/questions/18296035/how-to-extract-the-bits-of-larger-numeric-numpy-data-types


    ```python
    >>> bit_array = np.random.randint(5, size=[3,3])
    array([[1, 1, 3],
           [4, 2, 0],
           [4, 3, 2]], dtype=uint8)

    # Unpack 8 bits (8*1, as itemsize of uint8 is 1)
    >>> unpackbits(bit_array, 8)
    array([[[1, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0]],
           [[0, 0, 1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]],
           [[0, 0, 1, 0, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0]]], dtype=uint8)
    ```

    Args:
        array (np.ndarray): Array to unpack
        nof_bits (int): Number of bits to unpack

    Returns:
        np.ndarray: Unpacked array
    """
    return rasters_rio.unpackbits(array, nof_bits)


def read_bit_array(bit_mask: Union[xr.DataArray, np.ndarray],
                   bit_id: Union[list, int]) -> Union[np.ndarray, list]:
    """
    Read bit arrays as a succession of binary masks (sort of read a slice of the bit mask, slice number bit_id)

    ```python
    >>> bit_array = np.random.randint(5, size=[3,3])
    array([[1, 1, 3],
           [4, 2, 0],
           [4, 3, 2]], dtype=uint8)

    # Get the 2nd bit array
    >>> read_bit_array(bit_array, 2)
    array([[0, 0, 0],
           [1, 0, 0],
           [1, 0, 0]], dtype=uint8)
    ```

    Args:
        bit_mask (np.ndarray): Bit array to read
        bit_id (int): Bit ID of the slice to be read
          Example: read the bit 0 of the mask as a cloud mask (Theia)

    Returns:
        Union[np.ndarray, list]: Binary mask or list of binary masks if a list of bit_id is given
    """
    if isinstance(bit_mask, xr.DataArray):
        bit_mask = bit_mask.data

    return rasters_rio.read_bit_array(bit_mask, bit_id)


def read_uint8_array(bit_mask: Union[xr.DataArray, np.ndarray],
                     bit_id: Union[list, int]) -> Union[np.ndarray, list]:
    """
    Read 8 bit arrays as a succession of binary masks.

    Forces array to `np.uint8`.

    See `read_bit_array`.

    Args:
        bit_mask (np.ndarray): Bit array to read
        bit_id (int): Bit ID of the slice to be read
          Example: read the bit 0 of the mask as a cloud mask (Theia)

    Returns:
        Union[np.ndarray, list]: Binary mask or list of binary masks if a list of bit_id is given
    """
    return read_bit_array(bit_mask.astype(np.uint8), bit_id)


def set_metadata(naked_xda: xr.DataArray, mtd_xda: xr.DataArray, new_name=None) -> xr.DataArray:
    """
    Set metadata from a `xr.DataArray` to another (including `rioxarray` metadata such as encoded_nodata and crs).

    Useful when performing operations on xarray that result in metadata loss such as sums.

    ```python
    >>> # xda: some xr.DataArray
    >>> sum = xda + xda  # Sum loses its metadata here
    <xarray.DataArray 'xda' (band: 1, y: 322, x: 464)>
    array([[[nan, nan, nan, ..., nan, nan, nan],
            [nan, nan, nan, ..., nan, nan, nan],
            [nan, nan, nan, ..., nan, nan, nan],
            ...,
            [nan, nan, nan, ...,  2., nan, nan],
            [nan, nan, nan, ...,  2., nan, nan],
            [nan, nan, nan, ...,  2., nan, nan]]])
    Coordinates:
      * band         (band) int32 1
      * y            (y) float64 4.798e+06 4.798e+06 ... 4.788e+06 4.788e+06
      * x            (x) float64 5.411e+05 5.411e+05 ... 5.549e+05 5.55e+05

    >>> # We need to set the metadata back (and we can set a new name)
    >>> sum = set_metadata(sum, xda, new_name="sum")
    <xarray.DataArray 'sum' (band: 1, y: 322, x: 464)>
    array([[[nan, nan, nan, ..., nan, nan, nan],
            [nan, nan, nan, ..., nan, nan, nan],
            [nan, nan, nan, ..., nan, nan, nan],
            ...,
            [nan, nan, nan, ...,  2., nan, nan],
            [nan, nan, nan, ...,  2., nan, nan],
            [nan, nan, nan, ...,  2., nan, nan]]])
    Coordinates:
      * band         (band) int32 1
      * y            (y) float64 4.798e+06 4.798e+06 ... 4.788e+06 4.788e+06
      * x            (x) float64 5.411e+05 5.411e+05 ... 5.549e+05 5.55e+05
        spatial_ref  int32 0
    Attributes: (12/13)
        grid_mapping:              spatial_ref
        BandName:                  Band_1
        RepresentationType:        ATHEMATIC
        STATISTICS_COVARIANCES:    0.2358157950609785
        STATISTICS_MAXIMUM:        2
        STATISTICS_MEAN:           1.3808942647686
        ...                        ...
        STATISTICS_SKIPFACTORX:    1
        STATISTICS_SKIPFACTORY:    1
        STATISTICS_STDDEV:         0.48560665546817
        STATISTICS_VALID_PERCENT:  80.07
        original_dtype:            uint8
        _FillValue:                nan
    ```

    Args:
        naked_xda (xr.DataArray): DataArray to complete
        mtd_xda (xr.DataArray): DataArray with the correct metadata
        new_name (str): New name for naked DataArray

    Returns:
        xr.DataArray: Complete DataArray
    """
    naked_xda.rio.write_crs(mtd_xda.rio.crs, inplace=True)
    naked_xda.rio.update_attrs(mtd_xda.attrs, inplace=True)
    naked_xda.rio.set_nodata(mtd_xda.rio.nodata, inplace=True)
    naked_xda.encoding = mtd_xda.encoding

    if new_name:
        naked_xda = naked_xda.rename(new_name)

    return naked_xda


def set_nodata(xda: xr.DataArray, nodata_val: Union[float, int]) -> xr.DataArray:
    """
    Set nodata to a xarray that have no default nodata value.

    In the data array, the no data will be set to `np.nan`.
    The encoded value can be retrieved with `xda.rio.encoded_nodata`.

    ```python
    >>> A = xr.DataArray(dims=("x", "y"), data=np.zeros((3,3), dtype=np.uint8))
    >>> A[0, 0] = 1
    <xarray.DataArray (x: 3, y: 3)>
    array([[1, 0, 0],
           [0, 0, 0],
           [0, 0, 0]], dtype=uint8)
    Dimensions without coordinates: x, y

    >>> A_nodata = set_nodata(A, 0)
    <xarray.DataArray (x: 3, y: 3)>
    array([[ 1., nan, nan],
           [nan, nan, nan],
           [nan, nan, nan]])
    Dimensions without coordinates: x, y
    ```

    Args:
        xda (xr.DataArray): DataArray
        nodata_val (Union[float, int]): Nodata value

    Returns:
        xr.DataArray: DataArray with nodata set
    """
    xda_nodata = xr.where(xda.data == nodata_val, np.nan, xda)
    xda_nodata.rio.write_nodata(np.nan)
    xda_nodata.encoding["_FillValue"] = nodata_val
    return xda_nodata

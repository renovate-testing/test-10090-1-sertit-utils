# -*- coding: utf-8 -*-
# Copyright 2021, SERTIT-ICube - France, https://sertit.unistra.fr/
# This file is part of sertit-utils project
#     https://github.com/sertit/sertit-utils
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Script testing vector functions """
import os

import geopandas as gpd
import pytest
from shapely import wkt

from CI.SCRIPTS.script_utils import GEO_DATA
from sertit import ci, vectors
from sertit.vectors import WGS84


def test_vectors():
    """Test geo functions"""
    kml_path = os.path.join(GEO_DATA, "aoi.kml")
    wkt_path = os.path.join(GEO_DATA, "aoi.wkt")
    utm_path = os.path.join(GEO_DATA, "aoi.geojson")

    # KML
    vectors.set_kml_driver()  # An error will occur afterwards if this fails (we are attempting to open a KML file)

    # KML to WKT
    aoi_str_test = vectors.get_aoi_wkt(kml_path, as_str=True)
    aoi_str = (
        "POLYGON Z ((46.1947755465253067 32.4973553439109324 0.0000000000000000, "
        "45.0353174370802520 32.4976496856158974 0.0000000000000000, "
        "45.0355748149750283 34.1139970085580018 0.0000000000000000, "
        "46.1956059695554089 34.1144793800670882 0.0000000000000000, "
        "46.1947755465253067 32.4973553439109324 0.0000000000000000))"
    )
    assert aoi_str == aoi_str_test

    aoi = vectors.get_aoi_wkt(kml_path, as_str=False)

    # WKT to WKT
    aoi2 = vectors.get_aoi_wkt(wkt_path, as_str=False)

    # UTM to WKT
    aoi3 = vectors.get_aoi_wkt(utm_path, as_str=False)

    assert aoi.equals(aoi2)  # No reprojection, shoul be equal
    assert aoi.almost_equals(aoi3)  # Reprojection, so almost equal
    assert wkt.dumps(aoi) == aoi_str

    # UTM and bounds
    aoi = gpd.read_file(kml_path)
    assert "EPSG:32638" == vectors.corresponding_utm_projection(
        aoi.centroid.x, aoi.centroid.y
    )
    env = aoi.envelope[0]
    from_env = vectors.from_bounds_to_polygon(*vectors.from_polygon_to_bounds(env))
    assert env.bounds == from_env.bounds

    # GeoDataFrame
    geodf = vectors.get_geodf(env, aoi.crs)  # GeoDataFrame from Polygon
    ci.assert_geom_equal(geodf.geometry, aoi.envelope)
    ci.assert_geom_equal(
        vectors.get_geodf(geodf.geometry, aoi.crs), geodf
    )  # GeoDataFrame from Geoseries
    ci.assert_geom_equal(
        vectors.get_geodf([env], aoi.crs), geodf
    )  # GeoDataFrame from list of poly

    with pytest.raises(TypeError):
        vectors.get_geodf([1, 2, 3, 4, 5], aoi.crs)
    with pytest.raises(TypeError):
        vectors.get_geodf([1, 2], aoi.crs)


def test_gml():
    """Test GML functions"""
    empty_gml = os.path.join(GEO_DATA, "empty.GML")
    not_empty_gml = os.path.join(GEO_DATA, "not_empty.GML")
    not_empty_true = os.path.join(GEO_DATA, "not_empty_true.geojson")

    # Empty
    empty_gdf = gpd.GeoDataFrame(geometry=[], crs=WGS84)
    empty = vectors.open_gml(empty_gml)
    ci.assert_geom_equal(empty, empty_gdf)

    # Not empty
    not_empty = vectors.open_gml(not_empty_gml)
    ci.assert_geom_equal(not_empty, gpd.read_file(not_empty_true))

import setuptools

from sertit import (
    __author__,
    __author_email__,
    __description__,
    __documentation__,
    __title__,
    __url__,
    __version__,
)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
        "tqdm",
        "lxml",
        "psutil",
        "geopandas>=0.9.0",
        "cloudpathlib[all]",
    ],
    extras_require={
        "colorlog": ["colorlog"],
        "full": [
            "xarray>=0.18.0",
            "rasterio[s3]>=1.2.2",
            "rioxarray>=0.9.1",
            "colorlog",
            "dask[complete]",
        ],
        "rasters_rio": ["rasterio[s3]>=1.2.2"],
        "rasters": ["xarray>=0.18.0", "rasterio[s3]>=1.2.2", "rioxarray>=0.9.1"],
        "dask": [
            "xarray>=0.18.0",
            "rasterio[s3]>=1.2.2",
            "rioxarray>=0.9.1",
            "dask[complete]",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    package_data={"": ["LICENSE", "NOTICE"]},
    include_package_data=True,
    python_requires=">=3.7",
    project_urls={
        "Bug Tracker": f"{__url__}/issues/",
        "Documentation": __documentation__,
        "Source Code": __url__,
    },
)

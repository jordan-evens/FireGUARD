SET PYTHON=python-2.7.18.msi
if not exist "%PYTHON%" (
    PowerShell Invoke-WebRequest -Uri "https://www.python.org/ftp/python/2.7.18/%PYTHON%" -OutFile %PYTHON%
)

msiexec /q /i %PYTHON% TARGETDIR=C:\Python27\ArcGIS10.3 ALLUSERS=1
python -m pip install --upgrade pip
pip install --upgrade wheel
pip install "numpy-1.16.6+mkl-cp27-cp27m-win32.whl"
pip install GDAL-2.2.4-cp27-cp27m-win32.whl
pip install rasterio-1.0.28-cp27-cp27m-win32.whl
pip install pyproj-1.9.6-cp27-cp27m-win32.whl

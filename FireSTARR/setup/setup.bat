echo off

net session >nul 2>&1
IF NOT %ERRORLEVEL%==0 echo Must run as administrator in elevated command prompt && goto :end

IF DEFINED ENV_IS_SET goto :build
SET ENV_IS_SET=1
set VSCMD_DEBUG=1
SET VC_VARS=vcvars64.bat
for /r "C:\Program Files (x86)\Microsoft Visual Studio" %%a in (*) do if "%%~nxa"=="%VC_VARS%" set p=%%~dpnxa
call "%p%"

:build
pushd ..
@rem add sed to the path
pushd ..\WeatherSHIELD\db\sed\bin
SET PATH=%CD%;%PATH%
popd

git clone https://github.com/Microsoft/vcpkg.git
pushd vcpkg
call  .\bootstrap-vcpkg.bat
@rem ~ vcpkg.exe install sqlite3[core,tool]:x86-windows tiff:x86-windows curl:x86-windows libjpeg-turbo:x86-windows
vcpkg.exe install sqlite3[core,tool]:x64-windows tiff:x64-windows curl:x64-windows libjpeg-turbo:x64-windows
popd

git clone https://github.com/OSGeo/PROJ.git
pushd PROJ
git checkout tags/5.2.0
nmake /f makefile.vc
popd

git config --global http.sslVerify false
git clone https://gitlab.com/libtiff/libtiff.git
git config --global --unset http.sslVerify
git clone https://github.com/OSGeo/libgeotiff.git
@rem ~ wget https://download.osgeo.org/osgeo4w/osgeo4w-setup-x86_64.exe
@rem ~ @rem fix wrong permissions after download
@rem ~ icacls osgeo4w-setup-x86_64.exe /t /q /c /reset

@rem ~ osgeo4w-setup-x86_64.exe -q -k -r -A -s http://download.osgeo.org/osgeo4w/ -a x86_64 -R c:\OSGeo4W -P proj,libtiff,libgeotiff
pushd libtiff
git checkout Release-v3-9-3
nmake /f Makefile.vc
popd

pushd libgeotiff\libgeotiff
git checkout 1.4.3
sed -i "s/OSGEO4W =.*/OSGEO4W = \.\.\\\.\.\\libtiff\\libtiff/g" Makefile.vc
sed -i "s/\(TIFF_INC = .*\)\\include/\1/g" Makefile.vc
sed -i "s/\(TIFF_LIB_DLL = .*\)\\lib\\libtiff_i.lib/\1\\libtiff_i.lib/g" Makefile.vc
sed -i "s/\(INCL\t= .*\)/\1 -I ..\\..\\PROJ\\src/g" Makefile.vc
nmake /f Makefile.vc
popd

popd

:end


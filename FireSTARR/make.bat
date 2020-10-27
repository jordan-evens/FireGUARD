@echo off
IF DEFINED ENV_IS_SET goto :build
SET ENV_IS_SET=1
set VSCMD_DEBUG=1
SET VC_VARS=vcvarsx86_amd64.bat
for /r "C:\Program Files (x86)\Microsoft Visual Studio" %%a in (*) do if "%%~nxa"=="%VC_VARS%" set p=%%~dpnxa
call "%p%"

:build
SET Platform=
msbuild /p:Configuration=Release /m

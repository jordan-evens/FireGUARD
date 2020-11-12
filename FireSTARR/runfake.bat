@echo off
IF DEFINED ENV_IS_SET goto :build
SET ENV_IS_SET=1
set VSCMD_DEBUG=1
SET VC_VARS=vcvarsx86_amd64.bat
for /r "C:\Program Files (x86)\Microsoft Visual Studio" %%a in (*) do if "%%~nxa"=="%VC_VARS%" set p=%%~dpnxa
call "%p%"

:build
@rem clear this because it causes changes to where project builds and other things
SET Platform=
SET ARGS=-ArgumentList 'runfake.py TST123 2017-08-27 12:15 52.01 -89.024 test --wx C:\FireGUARD\FireSTARR\Data\output\wx.csv --ffmc 90 --dmc 40 --dc 300 --apcp_0800 0'
IF "%*" NEQ "" SET ARGS=-ArgumentList 'runfake.py %*'
@rem ~ msbuild /p:Configuration=Release /t:Clean,Build /m /warnaserror || (set ERRORLEVEL=1 && goto :end)
msbuild /p:Configuration=Release /t:Build /m /warnaserror || (set ERRORLEVEL=1 && goto :end)
rmdir /s /q test\TST
PowerShell Measure-Command {start-process python.exe %ARGS% -Wait -NoNewWindow}

:end

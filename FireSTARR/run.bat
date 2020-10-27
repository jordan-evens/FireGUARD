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
SET ARGS=
IF "%*" NEQ "" SET ARGS=-ArgumentList '%*'
msbuild /p:Configuration=Release /t:Build /m /warnaserror || (set ERRORLEVEL=1 && goto :end)
PowerShell Measure-Command {start-process Release\firestarr.exe %ARGS% -Wait -NoNewWindow}

:end
%COMSPEC% /C exit %ERRORLEVEL% >nul

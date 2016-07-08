@echo off

title Toontown 2.0 Game Launcher

echo Choose your connection method!
echo.
echo #1 - Offline Mode
echo.

:selection

set INPUT=-1
set /P INPUT=Selection: 

if %INPUT%==1 (
    set TT_GAMESERVER=127.0.0.1
) else (
    goto selection
)

echo.

if %INPUT%==1 (
    set /P ttUsername="Username: "
) else (
    set /P TT_PLAYCOOKIE=Username: 
)

echo.

echo ===============================
echo Starting Toontown 2.0
echo ppython: "C:\Panda3D-1.10.0\python\ppython.exe"

if %INPUT%==1 (
    echo Username: %ttUsername%
) else (
    echo Username: %TT_PLAYCOOKIE%
)

echo Gameserver: %TT_GAMESERVER%
echo ===============================

cd ../../

:main
if %INPUT%==1 (
    "C:\Panda3D-1.10.0\python\ppython.exe" -m toontown.toonbase.ToontownStart
) else (
    "C:\Panda3D-1.10.0\python\ppython.exe" -m toontown.toonbase.ToontownStart
)
pause

goto main

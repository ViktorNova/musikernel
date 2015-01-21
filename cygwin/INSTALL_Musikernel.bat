REM Get current drive letter into WD.
for /F %%A in ('cd') do set WD=%%~dA


REM Store any existing mounts, unmount them, and replace with mounts to current drive letter.
cygwin64\bin\mount -m | cygwin64\bin\sed s/mount/"%WD%\/cygwin64\\/bin\\/mount"/ > cygwin64\tmp\mount.log
cygwin64\bin\umount -U
cygwin64\bin\mount -f %WD%cygwin64/ /
cygwin64\bin\mount -f %WD%cygwin64\bin /usr/bin
cygwin64\bin\mount -f %WD%cygwin64\lib /usr/lib

REM Set some general environment variables
set path=%path%;%WD%cygwin64\bin;%WD%cygwin64\usr\X11R6\bin
set ALLUSERSPROFILE=%WD%ProgramData
set ProgramData=%WD%ProgramData
set CYGWIN=nodosfilewarning


REM This specifies the login to use.
set USERNAME=musikernel
set HOME=/home/%USERNAME%
set GROUP=None
set GRP=

REM If this is the current user's first time running Cygwin, add them to /etc/passwd
for /F %%A in ('cygwin64\bin\mkpasswd.exe -c ^| cygwin64\bin\gawk.exe -F":" '{ print $5 }'') do set SID=%%A
findstr /m %SID% cygwin64\etc\passwd
if %errorlevel%==1 (
echo Adding a user for SID: %SID%
for /F %%A in ('cygwin64\bin\gawk.exe -F":" '/^%GROUP%/ { print $3 }' cygwin64/etc/group') do set GRP=%%A
)
if "%GRP%" neq "" (
echo Adding to Group number: %GRP%
cygwin64\bin\printf.exe "\n%USERNAME%:unused:1001:%GRP%:%SID%:%HOME%:/bin/bash" >> cygwin64\etc\passwd
)
set GRP=
set SID=
set GROUP=


REM Make a symlink from /curdrive to the current drive letter.
cygwin64\bin\rm.exe /curdrive
cygwin64\bin\ln.exe -s %WD% /curdrive

REM Cleanup and replace pre-existing mounts.
cygwin64\bin\rm.exe /curdrive
cygwin64\bin\umount -U
cygwin64\bin\bash cygwin64\tmp\mount.log
cygwin64\bin\rm cygwin64\tmp\mount.log


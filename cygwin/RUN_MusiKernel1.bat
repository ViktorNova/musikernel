REM Get current drive letter into WD.
for /F %%A in ('cd') do set WD=%%~dA

REM Set some general environment variables
set path=%WD%bin;%WD%usr\X11R6\bin;%path%
set ALLUSERSPROFILE=%WD%ProgramData
set ProgramData=%WD%ProgramData
set CYGWIN=nodosfilewarning

REM This specifies the login to use.
set USERNAME=musikernel
set HOME=/home/%USERNAME%
set GROUP=None
set GRP=

bin\umount -U
bin\rm.exe -rf "%HOME%"
bin\mkdir.exe "%HOME%"
bin\mount.exe -f "%USERPROFILE%" "%HOME%"

REM If this is the current user's first time running Cygwin, add them to /etc/passwd
for /F %%A in ('bin\mkpasswd.exe -c ^| bin\gawk.exe -F":" '{ print $5 }'') do set SID=%%A
findstr /m %SID% etc\passwd
if %errorlevel%==1 (
echo Adding a user for SID: %SID%
for /F %%A in ('bin\gawk.exe -F":" '/^%GROUP%/ { print $3 }' cygwin64/etc/group') do set GRP=%%A
)
if "%GRP%" neq "" (
echo Adding to Group number: %GRP%
bin\printf.exe "\n%USERNAME%:unused:1001:%GRP%:%SID%:%HOME%:/bin/bash" >> etc\passwd
)
set GRP=
set SID=
set GROUP=


REM Make a symlink from /curdrive to the current drive letter.
bin\rm.exe /curdrive
bin\ln.exe -s %WD% /curdrive

bin\bash --login -c "/bin/python3.2m /musikernel1/usr/bin/musikernel1"


REM Cleanup and replace pre-existing mounts.
bin\rm.exe /curdrive
bin\umount -U
bin\bash tmp\mount.log
bin\rm tmp\mount.log


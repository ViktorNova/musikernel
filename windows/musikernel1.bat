SET LOG="%HOMEDRIVE%%HOMEPATH%\musikernel1\mk.log"
start /REALTIME cmd /c python3.exe musikernel1 ^> %LOG% ^2^&^>^1

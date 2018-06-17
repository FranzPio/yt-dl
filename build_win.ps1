ren src\main.py yt-dl.py
python -m PyInstaller --noconfirm --windowed --icon "resources\ytdl_icon.ico" src\yt-dl.py
ren src\yt-dl.py main.py

$versionLine = Get-Content src\config.py | Where-Object { $_.Contains("VERSION") }
$versionString = ($versionLine -replace "VERSION = ", "") -replace '"', ""

(Get-Content installer.iss) -replace "CURR_VERSION", $versionString | Set-Content installer.iss
&"C:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe" installer.iss
(Get-Content installer.iss) -replace $versionString, "CURR_VERSION" | Set-Content installer.iss

$zipFileName = "yt-dl_$($versionString)_win32_portable.zip"
cd dist
&"C:\\Program Files\\7-Zip\\7z.exe" a -mm=Deflate -mx=9 -r $zipFileName yt-dl
cd ..
Move-Item -Path "dist\$($zipFileName)" -Force -Destination .
Option Explicit

Dim shell, fso, tempRoot, repoDir, zipFile, cmdFile, pythonExe, cmdText

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Clean, disposable checkout: no local Git repository is required.
tempRoot = shell.ExpandEnvironmentStrings("%TEMP%") & "\JobSpy_damarowen_latest"
repoDir = tempRoot & "\JobSpy_damarowen-main"
zipFile = tempRoot & "\JobSpy_damarowen-main.zip"
cmdFile = tempRoot & "\run.cmd"
pythonExe = repoDir & "\.venv312\Scripts\python.exe"

If fso.FolderExists(tempRoot) Then fso.DeleteFolder tempRoot, True
fso.CreateFolder tempRoot

cmdText = "@echo off" & vbCrLf & _
"setlocal" & vbCrLf & _
"echo ========================================" & vbCrLf & _
"echo   JobSpy - Fresh GitHub main checkout" & vbCrLf & _
"echo ========================================" & vbCrLf & _
"echo." & vbCrLf & _
"echo [1/4] Downloading current GitHub main..." & vbCrLf & _
"powershell -NoProfile -ExecutionPolicy Bypass -Command ""Invoke-WebRequest -UseBasicParsing 'https://github.com/adiatmad/JobSpy_damarowen/archive/refs/heads/main.zip' -OutFile '" & zipFile & "'""" & vbCrLf & _
"if errorlevel 1 goto :error" & vbCrLf & _
"echo [2/4] Extracting..." & vbCrLf & _
"powershell -NoProfile -ExecutionPolicy Bypass -Command ""Expand-Archive -LiteralPath '" & zipFile & "' -DestinationPath '" & tempRoot & "' -Force""" & vbCrLf & _
"if errorlevel 1 goto :error" & vbCrLf & _
"cd /d """ & repoDir & """" & vbCrLf & _
"echo [3/4] Preparing Python 3.12 environment..." & vbCrLf & _
"if not exist """ & pythonExe & """ py -3.12 -m venv .venv312" & vbCrLf & _
"if errorlevel 1 goto :error" & vbCrLf & _
"echo Installing current dependencies..." & vbCrLf & _
"""" & pythonExe & """ -m pip install -r requirements.txt" & vbCrLf & _
"if errorlevel 1 goto :error" & vbCrLf & _
"echo [4/4] Starting Streamlit..." & vbCrLf & _
"""" & pythonExe & """ -m streamlit run app.py" & vbCrLf & _
"goto :eof" & vbCrLf & _
":error" & vbCrLf & _
"echo." & vbCrLf & _
"echo ERROR: Launcher failed. Check the message above." & vbCrLf & _
"pause" & vbCrLf

Dim ts
Set ts = fso.CreateTextFile(cmdFile, True, False)
ts.Write cmdText
ts.Close

shell.Run "cmd /k """ & cmdFile & """", 1, False

Set ts = Nothing
Set shell = Nothing
Set fso = Nothing

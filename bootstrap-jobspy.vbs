Option Explicit

Dim shell, fso
Dim baseDir, repoDir, venvPython
Dim commandLine

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' The VBS can live anywhere. The repository will be created beside it.
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
repoDir = baseDir & "\JobSpy_damarowen"
venvPython = repoDir & "\.venv312\Scripts\python.exe"

' ------------------------------------------------------------
' Bootstrap / update / run
'
' - Clone the repository if it does not exist.
' - Refuse to overwrite local changes.
' - Fast-forward main to origin/main.
' - Create Python 3.12 venv if needed.
' - Install current requirements.
' - Launch Streamlit.
'
' This follows the repository's documented main branch/runtime.
' ------------------------------------------------------------

commandLine = _
    "cd /d """ & baseDir & """ && " & _
    "echo ======================================== && " & _
    "echo   JobSpy - Latest main launcher && " & _
    "echo ======================================== && " & _
    "echo. && " & _
    "if not exist """ & repoDir & "\.git""" & " (" & _
        "echo [1/4] Repository not found. Cloning main... && " & _
        "git clone --branch main --single-branch https://github.com/adiatmad/JobSpy_damarowen.git """ & repoDir & """ && " & _
    ") else (" & _
        "echo [1/4] Repository found. Checking local changes... && " & _
        "cd /d """ & repoDir & """ && " & _
        "git diff --quiet && git diff --cached --quiet || (" & _
            "echo ERROR: Local changes detected. && " & _
            "echo Commit or stash them before using this launcher. && " & _
            "pause && exit /b 1" & _
        ") && " & _
        "git checkout main && " & _
        "git fetch origin main && " & _
        "git merge --ff-only origin/main" & _
    ") && " & _
    "cd /d """ & repoDir & """ && " & _
    "echo. && " & _
    "echo [2/4] Preparing Python 3.12 environment... && " & _
    "if not exist """"" & venvPython & """"" (" & _
        "py -3.12 -m venv .venv312" & _
    ") && " & _
    "echo. && " & _
    "echo [3/4] Installing current dependencies... && " & _
    """" & venvPython & """ -m pip install -r requirements.txt && " & _
    "echo. && " & _
    "echo [4/4] Starting Streamlit... && " & _
    """" & venvPython & """ -m streamlit run app.py"

shell.Run "cmd /k """ & commandLine & """", 1, False

Set shell = Nothing
Set fso = Nothing

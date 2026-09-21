Option Explicit

Dim shell, fso, repoDir, commandLine
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repoDir = fso.GetParentFolderName(WScript.ScriptFullName)

commandLine = "cd /d """ & repoDir & """ && git status --short --branch && git checkout main && git pull --ff-only origin main && python -m streamlit run app.py"

shell.Run "cmd /k " & commandLine, 1, False

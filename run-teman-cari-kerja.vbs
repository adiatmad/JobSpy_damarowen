Option Explicit

Dim shell, fso, repoDir, venvPython, commandLine
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repoDir = fso.GetParentFolderName(WScript.ScriptFullName)
venvPython = repoDir & "\.venv312\Scripts\python.exe"

If Not fso.FileExists(venvPython) Then
    MsgBox "Python environment not found:" & vbCrLf & venvPython & vbCrLf & vbCrLf & "Create .venv312 and install requirements.txt first.", vbExclamation, "Teman Cari Kerja"
    WScript.Quit 1
End If

commandLine = "cd /d """ & repoDir & """ && git status --short --branch && git checkout main && git pull --ff-only origin main && """ & venvPython & """ -m streamlit run app.py"

shell.Run "cmd /k " & commandLine, 1, False

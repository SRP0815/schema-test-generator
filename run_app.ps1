$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppFile = Join-Path $ProjectDir "app.py"

Set-Location $ProjectDir
python -m streamlit run $AppFile --server.port 8501

@echo off
set FLASK_APP=src.app
set PYTHONPATH=%~dp0
echo Subindo servidor em http://localhost:5000 ...
venv\Scripts\flask run --debug --host=0.0.0.0 --port=5000

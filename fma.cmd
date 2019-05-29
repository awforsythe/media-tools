@echo off
pushd %~dp0
pipenv run python main.py %*
popd

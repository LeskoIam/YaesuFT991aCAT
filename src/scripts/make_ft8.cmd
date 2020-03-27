rm -rf dist
rm -rf build
rm ft8.spec

pyinstaller -F ft8.py

cp dist/ft8.exe bin/ft8.exe

rm -rf dist
rm -rf build
rm ft8.spec
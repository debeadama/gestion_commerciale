@echo off

echo    Installation de la base de donnees

echo.
set /p MYSQL_PASSWORD=Entrez le mot de passe MySQL root : 
echo.
echo [1/3] Creation de la base de donnees...
mysql -u root -p%MYSQL_PASSWORD% -e "CREATE DATABASE IF NOT EXISTS gestion_commerciale;"
if %errorlevel% neq 0 ( echo ERREUR ! & pause & exit /b 1 )
echo OK !
echo [2/3] Importation des tables et donnees...
mysql -u root -p%MYSQL_PASSWORD% < "%~dp0database\seed_data.sql"
if %errorlevel% neq 0 ( echo ERREUR ! & pause & exit /b 1 )
echo OK !
echo [3/3] Creation du fichier .env...
(
echo DB_HOST=localhost
echo DB_PORT=3306
echo DB_NAME=gestion_commerciale
echo DB_USER=root
echo DB_PASSWORD=%MYSQL_PASSWORD%
) > "%~dp0.env"
echo OK !
echo.

echo   Installation terminee avec succes !

pause
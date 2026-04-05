@echo off
setlocal enabledelayedexpansion

echo    Installation de la base de donnees

echo.
set /p MYSQL_PASSWORD=Entrez le mot de passe MySQL root :
echo.
echo [1/3] Creation de la base de donnees...
mysql -u root -p!MYSQL_PASSWORD! -e "DROP DATABASE IF EXISTS gestion_commerciale; CREATE DATABASE gestion_commerciale CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if !errorlevel! neq 0 ( echo ERREUR ! & pause & exit /b 1 )
echo OK !
echo [2/3] Importation des tables et donnees...
mysql -u root -p!MYSQL_PASSWORD! < "%~dp0database\schema.sql"
if !errorlevel! neq 0 ( echo ERREUR schema.sql ! & pause & exit /b 1 )
mysql -u root -p!MYSQL_PASSWORD! gestion_commerciale < "%~dp0database\add_indexes.sql"
if !errorlevel! neq 0 ( echo ERREUR add_indexes.sql ! & pause & exit /b 1 )
mysql -u root -p!MYSQL_PASSWORD! gestion_commerciale < "%~dp0database\seed_data.sql"
if !errorlevel! neq 0 ( echo ERREUR seed_data.sql ! & pause & exit /b 1 )
echo OK !
echo [3/3] Creation du fichier .env...
if not exist "%APPDATA%\SGC\" mkdir "%APPDATA%\SGC\"
set ENV_FILE=%APPDATA%\SGC\.env
echo DB_HOST=localhost>"%ENV_FILE%"
echo DB_PORT=3306>>"%ENV_FILE%"
echo DB_NAME=gestion_commerciale>>"%ENV_FILE%"
echo DB_USER=root>>"%ENV_FILE%"
echo DB_PASSWORD=!MYSQL_PASSWORD!>>"%ENV_FILE%"
echo.>>"%ENV_FILE%"
echo # Application>>"%ENV_FILE%"
echo APP_NAME=Systeme de Gestion Commerciale>>"%ENV_FILE%"
echo APP_VERSION=1.0.0>>"%ENV_FILE%"
echo SESSION_TIMEOUT=300>>"%ENV_FILE%"
echo OK !
echo.

echo   Installation terminee avec succes !

pause
[Setup]
AppName=SGC - Système de Gestion Commerciale
AppVersion=1.0
AppPublisher=Soro Débé Adama
DefaultDirName={autopf}\SGC
DefaultGroupName=SGC
OutputDir=installer_output
OutputBaseFilename=SGC_Setup_Local_v1.0
SetupIconFile=assets\logo_SGC.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Icônes supplémentaires"

[Files]
Source: "dist\SGC.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SGC"; Filename: "{app}\SGC.exe"
Name: "{userdesktop}\SGC"; Filename: "{app}\SGC.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SGC.exe"; Description: "Lancer SGC"; Flags: nowait postinstall skipifsilent
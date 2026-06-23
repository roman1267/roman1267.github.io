Haunted Mansion Escape - Offline Installation Notes

1) Launch the game:
   - Run HauntedMansionEscape.exe
   - Or use the Start Menu shortcut

2) No-Python requirement:
   - Python is not required on the target machine.

3) Save/load behavior:
   - The game runs without MongoDB, but save/load is disabled.
   - To enable save/load, run:
     Start-Save-DB.bat
   - The script requests admin rights and will try to install Docker Desktop automatically via winget if missing.
   - This starts a local container named haunted-mansion-mongo on port 27017.
   - If the game is already open, restart it after MongoDB starts.

4) Stop save database when done:
   - Run Stop-Save-DB.bat

5) Troubleshooting:
   - If save/load fails, ensure Docker Desktop is running.
   - If automatic Docker install fails, install Docker Desktop manually and run Start-Save-DB.bat again.
   - If another service already uses port 27017, stop it and run Start-Save-DB.bat again.
   - Setup log is written to: %TEMP%\haunted-mongo-setup.log
   - If startup fails, re-run installer and launch from Start Menu.

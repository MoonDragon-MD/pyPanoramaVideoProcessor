#!/bin/bash

# Shows the main installer window
(
    while true; do
        sleep 1
    done
) | zenity --progress --width=600 --height=500 --title="Installatore per pyPanoramaVideoProcessor by MoonDragon" \
    --text="<b>Installer for pyPanoramaVideoProcessor by MoonDragon</b>\n\nVersion: 1.0.0\n\nhttps://github.com/MoonDragon-MD/pyPanoramaVideoProcessor\n\nThe installation wizard will follow including dependencies and shortcut on the menu" \
    --no-cancel --auto-close --pulsate &

INSTALLER_PID=$!

# Function to show a popup with the command to execute
show_command_popup() {
    zenity --error --width=400 --text="Error: $1 not found.\nRun the following command:\n\n<b>$2</b>"
}

# Check dependencies
if ! zenity --question --width=400 --text="Do you want to check and install dependencies?"; then
    INSTALL_DEPENDENCIES=false
else
    INSTALL_DEPENDENCIES=true
fi

if [ "$INSTALL_DEPENDENCIES" = true ]; then
    # Verifica Python3
    if ! command -v python3 &> /dev/null; then
        show_command_popup "Python3" "sudo apt-get install python3"
        kill $INSTALLER_PID
        exit 1
    fi

    # Verify pip
    if ! command -v pip3 &> /dev/null; then
        show_command_popup "pip3" "sudo apt-get install python3-pip"
        kill $INSTALLER_PID
        exit 1
    fi

    # Install Python dependencies
    zenity --info --width=400 --text="Installing Python dependencies..."
    pip3 install PyQt5 opencv-python
fi

# Asks the user where to install pyPanoramaVideoProcessor
INSTALL_DIR=$(zenity --file-selection --directory --title="Select the installation directory for pyPanoramaVideoProcessor" --width=400)
if [ -z "$INSTALL_DIR" ]; then
    zenity --error --width=400 --text="No directories selected.\nInstallation cancelled."
    kill $INSTALLER_PID
    exit 1
fi

# Crea il desktop entry
zenity --info --width=400 --text="By creating the shortcut in the applications menu..."
cat > ~/.local/share/applications/pyPanoramaVideoProcessor.desktop << EOL
[Desktop Entry]
Name=pyPanoramaVideoProcessor
Comment="Convert vertical video to horizontal by creating a panorama"
Exec=$INSTALL_DIR/pyPanoramaVideoProcessor/pyPanoramaVideoProcessor.sh
Icon=$INSTALL_DIR/pyPanoramaVideoProcessor/icon.png
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
EOL

# Create installation directory if it does not exist
mkdir -p "$INSTALL_DIR"

# Copia i file necessari
zenity --info --width=400 --text="By installing the application..."
cp -r pyPanoramaVideoProcessor "$INSTALL_DIR/"

# Genera lo script pyPanoramaVideoProcessor.sh
cat > "$INSTALL_DIR/pyPanoramaVideoProcessor/pyPanoramaVideoProcessor.sh" << EOL
#!/bin/bash
cd $INSTALL_DIR/pyPanoramaVideoProcessor/
python3 pyPanoramaVideoProcessor.py
EOL

# Rende eseguibile lo script pyPanoramaVideoProcessor.sh
chmod +x "$INSTALL_DIR/pyPanoramaVideoProcessor/pyPanoramaVideoProcessor.sh"

# Closes the main installer window
kill $INSTALLER_PID

zenity --info --width=400 --text="Installation complete!"
zenity --info --width=400 --text="You can launch pyPanoramaVideoProcessor from the applications menu"

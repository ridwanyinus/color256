
#!/bin/bash

# Simple script to update my_material theme from noctalia colors.json
# Usage: ./update_theme.sh [custom_output_path]

THEME_DIR="/home/ridwan/color256"
NOCTALIA_COLORS="/home/ridwan/dotfiles/noctalia/.config/noctalia/colors.json"
OUTPUT_PATH=${1:-"$THEME_DIR/themes/my_material.txt"}

cd "$THEME_DIR"
python3 convert_noctalia.py "$NOCTALIA_COLORS" "$OUTPUT_PATH"

# Function to reload applications
reload_applications() {
    echo "Reloading applications..."
    
    # Reload Kitty if running
    if pgrep -x "kitty" > /dev/null; then
        echo "  Reloading Kitty..."
        # Add small delay to ensure config is written before signaling
        sleep 0.1
        # Send signal to all Kitty processes
        pkill -USR1 -x kitty 2>/dev/null || echo "    Could not reload Kitty (try restarting manually)"
        # Alternative: use killall for more reliable signaling
        # killall -USR1 kitty 2>/dev/null || echo "    Could not reload Kitty (try restarting manually)"
    fi
    
    # Reload Ghostty if running
    if pgrep -x "ghostty" > /dev/null; then
        echo "  Ghostty config updated (restart required)"
    fi
    
    # Reload WezTerm if running
    if pgrep -x "wezterm" > /dev/null; then
        echo "  WezTerm config updated (restart required)"
    fi
    
    # Reload Alacritty if running
    if pgrep -x "alacritty" > /dev/null; then
        echo "  Alacritty config updated (restart required)"
    fi
    
    # Reload Foot if running
    if pgrep -x "foot" > /dev/null; then
        echo "  Reloading Foot..."
        pkill -USR1 foot 2>/dev/null || echo "    Could not reload Foot (try restarting manually)"
    fi
    
    # Reload X resources for st and other X11 apps
    if [ -n "$DISPLAY" ]; then
        echo "  Reloading X resources..."
        xrdb -merge ~/.Xresources 2>/dev/null || echo "    Could not reload X resources"
    fi
}

# Update Kitty config
if python3 main.py --generate kitty "$OUTPUT_PATH" > ~/.config/kitty/my_material.conf; then
    KITTY_SUCCESS="Kitty config updated"
else
    KITTY_SUCCESS="Failed to update Kitty config"
fi

# Update other terminal configs (optional, create them if they don't exist)
UPDATE_OTHER=${2:-"true"}
if [ "$UPDATE_OTHER" = "true" ]; then
    echo "Updating other terminal configs..."
    
    # Ghostty
    mkdir -p ~/.config/ghostty
    if python3 main.py --generate ghostty "$OUTPUT_PATH" > ~/.config/ghostty/my_material.conf; then
        echo "  Ghostty config updated"
    fi
    
    # WezTerm
    mkdir -p ~/.config/wezterm
    if python3 main.py --generate wezterm "$OUTPUT_PATH" > ~/.config/wezterm/my_material.lua; then
        echo "  WezTerm config updated"
    fi
    
    # Alacritty
    mkdir -p ~/.config/alacritty
    if python3 main.py --generate alacritty "$OUTPUT_PATH" > ~/.config/alacritty/my_material.yml; then
        echo "  Alacritty config updated"
    fi
    
    # Foot
    mkdir -p ~/.config/foot
    if python3 main.py --generate foot "$OUTPUT_PATH" > ~/.config/foot/my_material.ini; then
        echo "  Foot config updated"
    fi
    
    # X resources (for st and other X apps)
    if python3 main.py --generate xresources "$OUTPUT_PATH" > ~/.Xresources.my_material; then
        echo "  X resources updated"
    fi
fi

# Reload applications
reload_applications

echo ""
echo "Theme update complete!"
echo "  Source: $NOCTALIA_COLORS"
echo "  Output: $OUTPUT_PATH"
echo "  $KITTY_SUCCESS"
echo ""
echo "Debug info:"
echo "  Kitty processes: $(pgrep -x kitty | wc -l)"
echo "  Config file exists: $([ -f ~/.config/kitty/my_material.conf ] && echo "yes" || echo "no")"
echo "  Config file size: $([ -f ~/.config/kitty/my_material.conf ] && wc -c < ~/.config/kitty/my_material.conf || echo "0") bytes"
echo ""
echo "Tips:"
echo "  - Use './update_theme.sh path/to/output.txt false' to skip other terminal configs"
echo "  - Some terminals may require manual restart for full theme application"

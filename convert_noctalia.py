#!/usr/bin/env python3

import json
import sys
import os

def convert_noctalia_to_color256(noctalia_path, output_path="themes/my_material.txt"):
    """Convert noctalia colors.json to color256 theme format"""
    
    # Read the noctalia colors.json file
    try:
        with open(noctalia_path, 'r') as f:
            colors = json.load(f)
    except FileNotFoundError:
        print(f"Error: {noctalia_path} not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return False
    
    # Extract colors - map noctalia color names to standard 16-color palette
    # First 8 are normal colors, next 8 are bright/bold colors
    palette = []
    
    # Normal colors (0-7): black, red, green, yellow, blue, magenta, cyan, white
    palette.extend([
        colors.get('mSurface', '#141317').lstrip('#'),        
        colors.get('mError', '#ffb4ab').lstrip('#'),       
        colors.get('mPrimary', '#d2bbff').lstrip('#'),  
        colors.get('mTertiary', '#ffaeda').lstrip('#'),       
        colors.get('mSecondary', '#cdc1e1').lstrip('#'),   
        colors.get('mSurfaceVariant', '#211f23').lstrip('#'), 
        colors.get('mOnSurfaceVariant', '#cbc4d0').lstrip('#'), 
        colors.get('mOnSurface', '#e6e1e7').lstrip('#')      
    ])
    
    # Bright colors (8-15): bright black, red, green, yellow, blue, magenta, cyan, white
    palette.extend([
        colors.get('mShadow', '#000000').lstrip('#'),     
        colors.get('mOnError', '#690005').lstrip('#'),       
        colors.get('mOnPrimary', '#382461').lstrip('#'),  
        colors.get('mOnTertiary', '#541b3f').lstrip('#'),    
        colors.get('mOnSecondary', '#342c45').lstrip('#'),   
        colors.get('mOnHover', '#541b3f').lstrip('#'),    
        colors.get('mOutline', '#49454f').lstrip('#'), 
        colors.get('mOnSurface', '#e6e1e7').lstrip('#')       
    ])
    
    # Write the theme file
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as f:
        for i, color in enumerate(palette):
            if color and color.startswith('#'):
                color = color[1:]  # Remove # if present
            f.write(f"#{color}\n")
    
    print(f"Generated {output_path} with {len(palette)} colors (16-color palette)")
    return True

if __name__ == "__main__":
    # Default path to noctalia colors.json
    default_noctalia_path = "/home/ridwan/dotfiles/noctalia/.config/noctalia/colors.json"
    default_output_path = "themes/my_material.txt"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        noctalia_path = sys.argv[1]
    else:
        noctalia_path = default_noctalia_path
        
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = default_output_path
    
    success = convert_noctalia_to_color256(noctalia_path, output_path)
    sys.exit(0 if success else 1)

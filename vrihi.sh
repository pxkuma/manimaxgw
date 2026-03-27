#!/bin/bash

clear
echo -e "\e[1;36m"
cat << "ASCIIEOF"
██╗   ██╗██████╗ ██╗██╗  ██╗██╗
██║   ██║██╔══██╗██║██║  ██║██║
██║   ██║██████╔╝██║███████║██║
╚██╗ ██╔╝██╔══██╗██║██╔══██║██║
 ╚████╔╝ ██║  ██║██║██║  ██║██║
  ╚═══╝  ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝
ASCIIEOF
echo -e "\e[0m"

echo -e "\e[1;32m   >>> Vrihi - The Universal Video Pipeline <<<\e[0m\n"

# Ensure the target production directory exists on your Ubuntu host
mkdir -p ../Videos/production

# Check if Docker image exists
if ! docker image inspect ai-video-factory:latest >/dev/null 2>&1; then
    echo -e "\n❌ \e[31mError: Docker image 'ai-video-factory' not found.\e[0m"
    echo -e "Build it first with: \e[1;33mdocker build -t ai-video-factory .\e[0m\n"
    exit 1
fi

echo -e "Choose your deployment mode:"
echo -e "  \e[1;33m[1]\e[0m AI Prompt -> Full Video (Script, TTS, Visuals)"
echo -e "  \e[1;33m[2]\e[0m Python File -> Visuals Only (e.g., sin.py)"
echo ""
read -p "Enter 1 or 2: " MODE

if [ "$MODE" == "1" ]; then
    echo ""
    read -p "🎬 Enter your video topic: " TOPIC
    if [ -z "$TOPIC" ]; then
        echo -e "\n❌ \e[31mError: Topic cannot be empty.\e[0m"
        exit 1
    fi
    
    # Generate a clean, unique filename: e.g., "sine_waves_20260327_153045.mp4"
    SAFE_TOPIC=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd 'a-z0-9_')
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    FINAL_NAME="${SAFE_TOPIC}_${TIMESTAMP}.mp4"

    echo -e "\n🚀 Booting Vrihi AI Engine for: \e[1;36m$TOPIC\e[0m\n"
    docker run --rm --env-file .env -v "$(pwd)":/manim ai-video-factory python auto_video.py "$TOPIC"
    
    # Post-processing: Move and rename the output
    if [ -f "final_production.mp4" ]; then
        mv final_production.mp4 "../Videos/production/$FINAL_NAME"
        echo -e "\n🎉 \e[1;32mSUCCESS!\e[0m Video saved to: \e[1;36m../Videos/production/$FINAL_NAME\e[0m\n"
    else
        echo -e "\n❌ \e[31mError: final_production.mp4 not found. Render must have failed.\e[0m\n"
    fi

elif [ "$MODE" == "2" ]; then
    echo ""
    read -p "🐍 Enter the Python file to render (e.g., sin.py): " FILENAME
    if [ ! -f "$FILENAME" ]; then
        echo -e "\n❌ \e[31mError: File '$FILENAME' does not exist in this directory.\e[0m"
        exit 1
    fi
    
    # Generate unique filename based on the Python script name
    SAFE_NAME=$(basename "$FILENAME" .py)
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    FINAL_NAME="${SAFE_NAME}_render_${TIMESTAMP}.mp4"

    echo -e "\n🚀 Booting Vrihi Render Engine for: \e[1;36m$FILENAME\e[0m\n"
    docker run --rm --env-file .env -v "$(pwd)":/manim ai-video-factory python autorun.py "$FILENAME"
    
    # Grab the latest rendered file from the media folder and move it
    LATEST_RENDER=$(ls -t media/${SAFE_NAME}_full_render*.mp4 2>/dev/null | head -n 1)
    
    if [ -n "$LATEST_RENDER" ]; then
        mv "$LATEST_RENDER" "../Videos/production/$FINAL_NAME"
        echo -e "\n🎉 \e[1;32mSUCCESS!\e[0m Video saved to: \e[1;36m../Videos/production/$FINAL_NAME\e[0m\n"
    else
        echo -e "\n❌ \e[31mError: Could not find the rendered output in the media/ directory.\e[0m\n"
    fi

else
    echo -e "\n❌ \e[31mInvalid option. Exiting.\e[0m"
    exit 1
fi

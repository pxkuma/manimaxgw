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

# Ensure the target production directory exists
mkdir -p ../Videos/production

# --- Ollama Health Check ---
check_ollama() {
    local ollama_base="${OLLAMA_URL:-http://localhost:11434/api/generate}"
    # Extract base URL (remove /api/generate)
    local ollama_host="${ollama_base%/api/generate}"
    local model="${OLLAMA_MODEL:-deepseek-v3.1:671b-cloud}"
    
    echo -e "\e[1;33m[*] Checking Ollama connectivity...\e[0m"
    
    # Try to connect to Ollama
    if curl -sf "${ollama_host}/" > /dev/null 2>&1; then
        echo -e "\e[1;32m  ✓ Ollama is reachable at ${ollama_host}\e[0m"
    else
        echo -e "\e[31m  ✗ Cannot reach Ollama at ${ollama_host}\e[0m"
        echo -e "    Make sure Ollama is running. If using Docker Compose, run: \e[1;33mdocker compose up -d\e[0m"
        return 1
    fi
    
    # Check if the model is available
    if curl -sf "${ollama_host}/api/tags" 2>/dev/null | grep -q "$model"; then
        echo -e "\e[1;32m  ✓ Model '${model}' is available\e[0m"
    else
        echo -e "\e[1;33m  ⚠ Model '${model}' not found. Pulling it now (this may take a while)...\e[0m"
        curl -sf "${ollama_host}/api/pull" -d "{\"name\": \"${model}\"}" || true
    fi
    
    echo ""
    return 0
}




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
    
    # Generate a clean, unique filename
    SAFE_TOPIC=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd 'a-z0-9_' | cut -c 1-50)
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    FINAL_NAME="${SAFE_TOPIC}_${TIMESTAMP}.mp4"

    echo -e "\n🚀 Booting Vrihi AI Engine for: \e[1;36m$TOPIC\e[0m\n"
    
    if [ -f /.dockerenv ]; then
        # Inside Docker container - Ollama is accessible via compose network
        check_ollama
        python auto_video.py "$TOPIC"
    else
        # On host - use host Ollama directly
        export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434/api/generate}"
        export OLLAMA_MODEL="${OLLAMA_MODEL:-deepseek-v3.1:671b-cloud}"
        # Activate venv if it exists
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate"
        fi
        check_ollama
        python auto_video.py "$TOPIC"
    fi
    
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
    if [ -f /.dockerenv ]; then
        python autorun.py "$FILENAME"
    else
        docker compose run --rm \
            --entrypoint bash \
            vrihi -c "python autorun.py '$FILENAME'"
    fi
    
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

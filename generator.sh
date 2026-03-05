source .env/bin/activate
source ./config.sh
uv run image_generator.py --output "$1" --prompt "$2"

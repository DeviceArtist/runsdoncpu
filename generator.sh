source .env/bin/activate
uv run image_generator.py --output "$1" --prompt "$2"

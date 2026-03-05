source .env/bin/activate
export HF_HOME=./cache/hf_cache
export TRANSFORMERS_CACHE=./cache/transformers_cache
export HF_ENDPOINT=https://xxx
uv run image_generator.py --output "$1" --prompt "$2"

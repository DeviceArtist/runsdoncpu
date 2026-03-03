source .env/bin/activate
uv run python xmpp_image_bot.py --jid "$1" --password "$2"
source .env/bin/activate
cource ./config.sh
uv run python xmpp_image_bot.py --jid "$1" --password "$2"

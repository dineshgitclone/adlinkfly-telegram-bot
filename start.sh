if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/dineshgitclone/adlinkfly-telegram-bot.git /adlinkfly-telegram-bot
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /adlinkfly-telegram-bot
fi
cd /adlinkfly-telegram-bot
pip3 install -U -r requirements.txt
echo "Starting Bot...."
python3 adlinkfly_bot.py

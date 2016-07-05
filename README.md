# bitshares2-liquiditybots


## Most of the liqbot specific code and development has been merged/moved into: [StakeMachine](https://github.com/xeroc/stakemachine), please go there if you want a Bitshares trading bot.

This docker-compose file runs a cli-wallet container and a bot that uses cli-wallet to connect with graphene.
cli-wallet connects to the openledger full node and the bot does as well. To switch to your own full node (you should if you are running a bot),
change "witness_url" in `./docker-exchangebot/exchangebot/config.py` and the -s option in `cli-wallet-start.sh`

## How to run this

You will find the full instructions at https://github.com/linouxis9/bitshares2-liquiditybots/releases

* Put a cli_wallet password in `./docker-exchangebot/exchangebot/config.py`
* Change account name in the same config file
* Tweak config.py further to your liking.
* Execute `docker-compose up` in the root directory
* Send funds to the account
* Restart docker-compose. (ctrl+c and docker-compose start)
* Check the output with `docker-compose logs`

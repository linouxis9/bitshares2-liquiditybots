# bitshares2-liquiditybots

## How to run this

* Put a cli_wallet password in `./docker-exchangebot/exchangebot/config.py`
* Change account name in the same config file
* Execute `docker-compose up` in the root directory
* Send funds to the account
* Restart docker-compose. (ctrl+c and docker-compose up)
* To start docker-compose in the background use `docker-compose start` and check the output with `docker-compose logs`

## Todo

* Make the script create a 1 out of 2 multisig account consisting of the bot-account and funding-liquidity-bot and let the bot use that account. (so we can fund an account and get the money back painlessly when it's inactive)
* Find out a way to monitor performance of the bots (the bot itself so it doesn't lose money and the market to see the effect the bots have on the market). cli_wallet market_history()?
* Create docker images for the raspberry pi
* Tweak bot parameters

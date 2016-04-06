# bitshares2-liquiditybots

## How to use the docker

* Put a cli_wallet password in `./docker-exchangebot/exchangebot/config.py`
* Change account name in the same config file
* Execute `docker-compose up` in the root directory
* Send funds to the account
* Restart docker-compose. (ctrl+c and docker-compose up)
* To start docker-compose in the background use `docker-compose start` and check the output with `docker-compose logs`

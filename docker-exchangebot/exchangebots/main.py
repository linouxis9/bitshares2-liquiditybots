import bot
import json
import time
import datetime
import requests
from grapheneapi import GrapheneAPI
from grapheneapi.grapheneapi import RPCError
from apscheduler.schedulers.background import BlockingScheduler


# Load the configuration
import config


def run_bot(bot=bot):
    print(str(datetime.datetime.now()) + ": Starting bot...")
    print(str(datetime.datetime.now()) + ": Cancelling orders...")
    bot.cancel_all()
    print(str(datetime.datetime.now()) + ": Sleeping")
    time.sleep(12)
    print(str(datetime.datetime.now()) + ": Running the bot")
    bot.execute()


def register_account_faucet(account, public_key, referrer=config.referrer, faucet=config.faucet):
    headers = {
		"Accept": "application/json",
		"Content-type": "application/json",
		"User-Agent": "LiquidityBots/1.0"
	}
    payload = {
                "account": {
                "name": account,
                "owner_key": public_key,
                "active_key": public_key,
                "memo_key": public_key,
                "refcode": referrer,
                "referrer": referrer
            }
        }
    #request = requests.post('http://testnet.bitshares.eu/api/v1/accounts', data=json.dumps(payload), headers=headers)
    request = requests.post(faucet + '/api/v1/accounts', data=json.dumps(payload), headers=headers)
    return (request.status_code == 201, request.text)


if __name__ == '__main__':
    time.sleep(1) # sleep to give the cli_wallet time to start

    # rpc connection
    rpc = GrapheneAPI(config.wallet_host, config.wallet_port, "", "")
    try:
        rpc.set_password(config.wallet_password) # try to set password
    except RPCError: # if RCPError the password is already set
        pass
    rpc.unlock(config.wallet_password) # unlock the wallet.

    my_accounts = rpc.list_my_accounts()

    if len(my_accounts) is 0:
        brain_key = rpc.suggest_brain_key()
        account_registered, account_registration_response = register_account_faucet(config.account, brain_key['pub_key'])
        if account_registered:
            rpc.import_key(config.account, brain_key['wif_priv_key'])

            print("Account: %s succesfully registered" % config.account)
            print(rpc.list_my_accounts())

            print("Brain key: %s" % brain_key['brain_priv_key'])
            print("Write it down/back it up ^")

            print("Send funds to %s and start the bot again" % config.account)
        else:
            print("Account creation failed")
            print(brain_key)
            print(faucet + " response: ", account_registration_response)

    else:
        print(my_accounts)
        print(config.account)
        print(rpc.list_account_balances(config.account))

        try:
            bot.init(config)
        except Exception as e:
            print(e)

        scheduler = BlockingScheduler()
        scheduler.add_job(run_bot, 'interval', hours=config.interval)
        scheduler.start()

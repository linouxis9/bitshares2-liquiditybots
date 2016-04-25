import bot
import json
import time
import datetime
import requests
from grapheneapi import GrapheneAPI
from grapheneapi.grapheneapi import RPCError
import config


def run_bot(bot=bot):
    rpc = GrapheneAPI(config.wallet_host, config.wallet_port, "", "")
    if rpc.is_locked():
        rpc.unlock(config.wallet_password)

    print(str(datetime.datetime.now()) + ": Starting bot...")
    bot.init(config)
    time.sleep(6)
    print(str(datetime.datetime.now()) + ": Running the bot")
    bot.run()

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
    request = requests.post(faucet + '/api/v1/accounts', data=json.dumps(payload), headers=headers)
    return (request.status_code == 201, request.text)


if __name__ == '__main__':
    time.sleep(5) # sleep to give the cli_wallet time to start
    rpc = GrapheneAPI(config.wallet_host, config.wallet_port, "", "")
    try:
        rpc.set_password(config.wallet_password) # try to set password
    except RPCError: # if RCPError the password is already set
        pass
    rpc.unlock(config.wallet_password) # unlock the wallet.
    my_accounts = rpc.list_my_accounts()

    if len(my_accounts) == 0:
        brain_key = rpc.suggest_brain_key()
        account_registered, account_registration_response = register_account_faucet(config.account, brain_key['pub_key'])
        if account_registered:
            rpc.import_key(config.account, brain_key['wif_priv_key'])

            print("Account: %s successfully registered" % config.account)
            print(rpc.list_my_accounts())

            print("Brain key: %s" % brain_key['brain_priv_key'])
            print("Write it down/back it up ^")

            print("Send funds to %s and start the bot again" % config.account)
        else:
            print("Account creation failed")
            print(brain_key)
            print(config.faucet + " response: ", account_registration_response)
    else:
        print(my_accounts)
        print(config.account)
        print(rpc.list_account_balances(config.account))
        print("Bot config: " + str(config.bots))
        
        run_bot() # running the bot before the scheduler, otherwise it will run for the first time after config.interval
        #scheduler = BlockingScheduler()
        #scheduler.add_job(run_bot, 'interval', hours=config.interval)
        #scheduler.start()


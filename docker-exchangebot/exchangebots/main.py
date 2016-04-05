import bot
import json
import time
import datetime
import requests
from grapheneapi import GrapheneAPI
from grapheneapi.grapheneapi import RPCError


# Load the configuration
import config


def register_account_openledger(account, public_key, referrer=config.referrer, headers=config.headers):
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
    request = requests.post('https://bitshares.openledger.info/api/v1/accounts', data=json.dumps(payload), headers=headers)
    return (request.status_code == 201, request.text)
        
        
if __name__ == '__main__':
    time.sleep(1) # sleep to give the cli_wallet time to start
        
    # rpc connection
    rpc = GrapheneAPI(config.wallet_host, config.wallet_port, "", "")
    try:
        rpc.set_password(config.unlock_wallet_password) # try to set password
    except RPCError: # if RCPError the password is already set
        pass
    rpc.unlock(config.unlock_wallet_password) # unlock the wallet.
    
    my_accounts = rpc.list_my_accounts()
    
    if len(my_accounts) is 0:
        brain_key = rpc.suggest_brain_key()
        account_registered, account_registration_response = register_account_openledger(config.account, brain_key['pub_key'])  
        if account_registered:
            rpc.import_key(config.account, brain_key['wif_priv_key'])
            
            print("Account: %s succesfully registered" % config.account)
            print(rpc.list_my_accounts())
            
            print("Brain key: %s" % brain_key['brain_priv_key'])
            print("Write it down/back it up ^")

            print("Send funds to %s and start the bot again")
        else:
            print("Account creation failed")
            print(brain_key)
            print("Openledger response: ", account_registration_response)

    else:
        print(my_accounts)
        print(config.account)
        print(rpc.list_account_balances(config.account))
                
        try:
            bot.init(config)
        except Exception as e:
            print(e)
            
        
        while True:
            bot.cancel_all()
            print(str(datetime.datetime.now()) + ": sleep")
            time.sleep(60)
            print(str(datetime.datetime.now()) + ": bot.run()")
            bot.execute()
            
        bot.cancel_all()


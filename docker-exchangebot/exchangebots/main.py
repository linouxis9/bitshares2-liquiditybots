import bot
import time
import requests
from grapheneapi import GrapheneAPI
import json
import string
import random
import sys
import os
from grapheneapi.grapheneapi import RPCError
# Load the configuration
import config


if __name__ == '__main__':
    time.sleep(1)

    rpc = GrapheneAPI(config.wallet_host, config.wallet_port, "", "")

    try:
        rpc.set_password(config.unlock_wallet_password)
    except RPCError:
        rpc.unlock(config.unlock_wallet_password)
    else:
        rpc.unlock(config.unlock_wallet_password)

    my_accounts = rpc.list_my_accounts()

    if len(my_accounts) is 0:
        brain_key = rpc.suggest_brain_key()
        account_name = config.account

        headers = {"Accept": "application/json",
                    "Content-type": "application/json"}
        payload = {
            "account" : 
                { 
                "name" : account_name,
                "owner_key" : brain_key['pub_key'],
                "active_key" : brain_key['pub_key'],
                "memo_key" : brain_key['pub_key'],
                "refcode" : "bitshares-munich",
                "referrer" : "bitshares-munich"
            }
        }

        r = requests.post('https://bitshares.openledger.info/api/v1/accounts', data=json.dumps(payload), headers=headers)
        if r.status_code == 201:
            print("Account: %s succesfully registered" % account_name)

            print(rpc.import_key(account_name, brain_key['wif_priv_key']))
            print(rpc.list_my_accounts())
            print("Brain key: %s" % brain_key['brain_priv_key'])
            print("Write it down/back it up ^")

            print("Send funds to %s and start the bot again")
        else:
            print(r.status_code)
            print(r.text)
            print("Account creation failed")

 
    else:
        print(my_accounts)

        # initialize the bot infrastructure with our settings
        bot.init(config)

        # execute the bot(s) continuously and get notified via websocket
        bot.execute()

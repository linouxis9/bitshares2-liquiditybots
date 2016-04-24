#!/bin/bash

cli_wallet \
    -s wss://bitshares.openledger.info:8090/ws \
    -H 0.0.0.0:8092 \
    --wallet-file /wallet/wallet.json \
    -d

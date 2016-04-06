<?php

# Pretty simple faucet done in two minutes using GraphenePHP Library (which will be made available once my worker is ready)

require_once "../Blockchain.php";

$account_to_register = $_GET['account'];
$account_registrar = ""; // We need to create an LTM account
$public_key = $_GET['public_key'];

$Blockchain = new \GraphenePHP\OctoBitsharesBlockchain($account_registrar);

// I had to create these two functions on the library for this script to work

if ($Blockchain->Tools->is_not_premium($account_to_register)) {
  $Blockchain->Wallet->register_account($account_to_register, $account_registrar, $public_key);
  http_response_code(201); // I need to investigate the result of this call, to see what to return to the bot's script
  echo "OK";
} else {
  http_response_code(401);
  echo $account_to_register." is a premium account, therefore it cannot be registered.";
}

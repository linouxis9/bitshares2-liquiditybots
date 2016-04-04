<?php

# Pretty simple faucet done in two minutes using GraphenePHP Library (which will be mace available once my worker is ready)

require_once "../Blockchain.php";

$account_to_register = $_GET['account'];
$account_registrar = ""; // We need to create an LTM account
$public_key = $_GET['public_key'];

$Blockchain = new \GraphenePHP\OctoBitsharesBlockchain($account_registrar);

// I had to create these two functions on the library for this script to work

if ($Blockchain->Tools->is_not_premium($account_to_register)) {
  $Blockchain->Wallet->register_account($account_to_register, $account_registrar, $public_key);
  // I need to investigate the result of this call, to see what to return to the bot's script
}

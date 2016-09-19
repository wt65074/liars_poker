<?php



$port = $argv[1]
$folder = $argv[2];

if (!$message || !$folder)
    exit('Example Usage: $php newspush.php 10000 \Desktop\players.json' . "\n");

$json = file_get_contents($folder);

//Decode JSON
$json_data = json_decode($json,true);

//Print data
print_r($json_data);

// Put your device token here (without spaces):
$deviceTokens = $json_data['deviceTokens']

// Put your private key's passphrase here:
$passphrase = 'eighTnine9one!';

////////////////////////////////////////////////////////////////////////////////

// Create a stream and add a certificate and a passphrase
$ctx = stream_context_create();
stream_context_set_option($ctx, 'ssl', 'local_cert', 'ck.pem');
stream_context_set_option($ctx, 'ssl', 'passphrase', $passphrase);

// Open a connection to the APNS server
$fp = stream_socket_client(
  'ssl://gateway.sandbox.push.apple.com:2195', $err,
  $errstr, 60, STREAM_CLIENT_CONNECT|STREAM_CLIENT_PERSISTENT, $ctx);

if (!$fp)
  exit("Failed to connect: $err $errstr" . PHP_EOL);

echo 'Connected to APNS' . PHP_EOL;

// Create the payload body
$body['aps'] = array(
  'alert' => 'New Game Request',
  'sound' => 'default',
  'port' => $port,
  );

// Encode the payload as JSON
$payload = json_encode($body);

foreach($deviceTokens as $item) {
  // Build the binary notification
  $msg = chr(0) . pack('n', 32) . pack('H*', $item) . pack('n', strlen($payload)) . $payload;

  // Send it to the server
  $result = fwrite($fp, $msg, strlen($msg));
}

if (!$result)
  echo 'Message not delivered' . PHP_EOL;
else
  echo 'Message successfully delivered' . PHP_EOL;

// Close the connection to the server
fclose($fp);

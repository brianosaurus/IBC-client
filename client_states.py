#!/usr/bin/env python3

from http import client
import sys
import json
import subprocess
from dateutil.parser import parse


page = 1
clients = []

while True:
  output = subprocess.check_output(['umeed', 'q', 'ibc', 'client', 'states', '--output', 'json', '--node', sys.argv[1], '--page', str(page)])
  data = json.loads(output.decode('utf-8'))

  clients.extend(data['client_states'])

  #if not data['pagination']['next_key']: 
  break

  page += 1

# get the block time
output = subprocess.check_output(["umeed", "q", "ibc", "connection", "connections", "--output", "json", "--node", sys.argv[1]])
connections = json.loads(output.decode('utf-8'))

output = subprocess.check_output(["umeed", "q", "ibc", "channel", "channels", "--output", "json", "--node", sys.argv[1]])
channels = json.loads(output.decode('utf-8'))

for client in clients:
  current_block_number = connections['height']['revision_height']
  output = subprocess.check_output(["umeed", "q", "block", current_block_number, "--node", sys.argv[1]])
  current_block = json.loads(output.decode('utf-8')) 
  current_block_time = parse(current_block['block']['header']['time'])

  print(f"Current block time {current_block_time} and number {current_block_number}")
  print("")

  tried_connections = {}

  for connection in connections['connections']:
    if connection['client_id'] in tried_connections.keys():
      continue

    tried_connections[connection['client_id']] = True

    output = subprocess.check_output(['umeed', 'q', 'ibc', 'client', 'state', connection['client_id'], '--output', 'json', '--node', sys.argv[1]])
    data = json.loads(output.decode('utf-8'))

    revision_number = connections['height']['revision_number']
    revision_height = int(connections['height']['revision_height']) - 1
    print("client id: " + connection['client_id'])
    print('connection id: ' + connection['id'])
    print('counterparty connection id: ' + connection['counterparty']['connection_id'])
    print('counterparty client id: ' + connection['counterparty']['client_id'])
    print("revison: " + revision_number)
    print("revison height: " + str(revision_height))
    print('trusting period: ' + client['client_state']['trusting_period'])
    print('chain id', data['client_state']['chain_id'])

    try:
      #  umeed q ibc channel client-state transfer channel-9 --node https://rpc.cope.umeemania-1.network.umee.cc:443
      output = subprocess.check_output(['umeed', 'q', 'ibc', 'client', 'consensus-states', connection['client_id'], '--node', sys.argv[1], '--reverse', '--limit', '1', '--height', str(revision_height), '--output', 'json'])

      block = json.loads(output.decode('utf-8'))
      block_time = parse(block['consensus_states'][1]['consensus_state']['timestamp'])

      print("RPC endpoint block time: " + str(current_block_time))
      print("consensus block time: " + str(block_time))

      difference = (current_block_time - block_time).total_seconds()
      trust_period_int = int("".join(filter(str.isdigit, client['client_state']['trusting_period'])))

      if difference > int(trust_period_int):
        print(f"ERROR: Trusting period {trust_period_int} exceeded at {difference} seconds")
      else:
        print(f"{connection['client_id']} within trusting period {trust_period_int} with {difference}")
    except Exception as e:
      print('ERROR: ' + connection['client_id'] + ' not found: ' + str(e))

    print("")




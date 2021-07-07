from telethon import TelegramClient, sync, events
from apscheduler.schedulers.background import BackgroundScheduler
import json
from github import Github
import json
from web3 import Web3
from web3.contract import Contract
from datetime import datetime
import re
from config import config
import ast
import winsound


g = Github("8f4c3ad5f0d87a248a7cae8777c67d28c535e0ca")

def token_list_update():
    repo = g.get_repo("pancakeswap/pancake-swap-interface")
    contents = repo.get_contents("/src/constants/token/pancakeswap.json")
    token_list = json.loads(str(contents.decoded_content, 'utf-8'))
    with open("./configs/token_list.json", "w") as outfile: 
        json.dump(token_list, outfile)
    return token_list['tokens']

def token_list_sync():
    print('token_list_update')
    token_list = token_list_update()
    personal_list = json.load(open('./configs/personal_token_list.json'))['tokens']
    final_list = token_list + personal_list
    final_dict = {
        "tokens": final_list
    }
    with open("./configs/final_token_list.json", "w") as outfile: 
        json.dump(final_dict, outfile)  

def lookup_address_by_symbol(symbol):
    token_list = json.load(open('./configs/final_token_list.json'))['tokens']
    target_token = [token for token in token_list if token['symbol'].lower() == symbol.lower()]
    print("Token Contract Address: ", target_token[0]['address'])
    return target_token[0]['address'] if len(target_token)  >  0 else None

def create_transaction(c, wbnb_address, token_address, receiver_address, private_key, details, amountOutMin):
    transaction = c.functions.swapExactETHForTokens(amountOutMin, [wbnb_address, token_address], receiver_address, int(
        datetime.timestamp(datetime.now())) + 30*24*60*60).buildTransaction(details)
    signed_txn = w3.eth.account.signTransaction(transaction, private_key)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    winsound.Beep(700, 5000)
    return txn_hash.hex()


async def buy_token(symbol):
    address = lookup_address_by_symbol(symbol)
    if not address:
        return
    
    c = w3.eth.contract(abi=config['router_abi'],
                        address=config['pancake_router_address']) # Pancakeswap Router Instance
    
    wbnb_address = c.functions.WETH().call()
    token_address = Web3.toChecksumAddress(address)
    receiver_address = Web3.toChecksumAddress(usr_config['wallet_address'])
    private_key = usr_config['private_key']

    bnb_value = Web3.toWei(usr_config['bnb_value'], 'ether') # BNB to spend from config.json

    factory_address = c.functions.factory().call()
    (amountOutMin, decimals) = countAmountOutMin(token_address, wbnb_address, bnb_value, factory_address)  # Min amount of tokens to buy
    msg = '🎇🎇🎇\n**Buying**: {}\n**Address**: ```{}```\n**Min Amount**: {}'.format(symbol, address, amountOutMin / (10 ** decimals))
    output = '\nBuying: {}\nAddress: {}\nMin Amount: {}\n'.format(symbol, address, amountOutMin / (10 ** decimals))
    await send(msg)
    print(output)

    details = {
        'chainId': config['chainId'],  # same
        'gas': usr_config['gas'],  # same || estimate_gas
        'nonce': w3.eth.getTransactionCount(receiver_address),  # same
        'gasPrice': Web3.toWei(usr_config['gasPrice'], 'ether'),  # same
        # how much bnb to spend from config.json
        'value': bnb_value
    }

    try:
        return create_transaction(c, wbnb_address, token_address, receiver_address, private_key, details, int(amountOutMin))
    except Exception as err:
        return err

def countAmountOutMin(token, wbnb, bnb_value, factory):
    f = w3.eth.contract(abi=config['factory_abi'],
                        address=factory) # Pancakeswap Factory Instance
    pair = f.functions.getPair(token, wbnb).call()
    p = w3.eth.contract(abi=config['pair_abi'],
                        address=pair) # Pancakeswap Pair Instance
    token0 = p.functions.token0().call()
    token1 = p.functions.token1().call()
    decimals = p.functions.decimals().call()
    (res0, res1, timestamp) = p.functions.getReserves().call()
    k = res0 * res1
    
    slippage = float(usr_config['slippage_percentage']) # Slippage Percentage from config.json
    
    resToken = 0
    resWBNB = 0
    if(token0 == token and token1 == wbnb):
        resToken = res0
        resWBNB = res1
    elif(token1 == token and token0 == wbnb):
        resToken = res1
        resWBNB = res0
    
    if(resWBNB == 0): 
        return (0, decimals)
    #reserve updates due to slippage
    resWBNB = resWBNB * (1 + slippage / 100)
    resToken = k / resWBNB

    amountOutMin = resToken - k / (resWBNB + bnb_value)

    return (amountOutMin, decimals)

async def message_handler(message, containing_fields=['binance will list', 'innovation zone']):
    if not (containing_fields[0] in message.lower() and containing_fields[1] in message.lower()):
        return
    symbol = re.search('\(([^)]+)', message).group(1)
    response = await buy_token(symbol)
    print(response)

    if(str(type(response)) == "<class 'ValueError'>"):
        response = ast.literal_eval(str(response))
        response = '**Error Code**: {}\n**Error Message**: {}'.format(response['code'], response['message'])
    else:
        response = '**Transaction Hash**:\n```{}```'.format(str(response))
    await send(response)

async def send(msg):
    await client.send_message(to, msg)

usr_config = json.load(open('./configs/config.json'))
w3 = Web3(Web3.HTTPProvider(config['provider_url']))
to = usr_config['update_to']


scheduler = BackgroundScheduler()
client = TelegramClient('session_name', usr_config['api_id'], usr_config['api_hash'])

token_list_sync()
scheduler.add_job(token_list_sync, 'interval', hours=1)
scheduler.start()
client.start()

@client.on(events.NewMessage(chats=usr_config['channel']))
async def message_listenner(event): await message_handler(event.message.message)

with client:
    client.run_until_disconnected()

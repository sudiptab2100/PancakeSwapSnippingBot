# PancakeSwapSnippingBot

## Description:

- The bot keeps eye on Binance Announcements. Whenever binance announces a new token listing, the bot immediately buys the token from pancakeswap(if it is available on Pancakeswap)
- User gets notified about the coin listing and transaction details in telegram message

## Steps to configure the bot:

- Follow the official binance announcement channel on telegram - [Binance Announcements](https://t.me/binance_announcements)
- Goto https://my.telegram.org/apps & login using your telegram account  
  Get your api_id & api_hash 
- Clone the repo and install following python packages
  - telethon
  - web3
  - github
- Now goto configs/config.json file and configure it with your details
  - Set your api_id of telegram
  - Set your api_hash of telegram
  - Set wallet address
  - Set private key of that wallet address(not mnemonic)
  - Set the bnb value(the amount that will be used to buy tokens)
  - Set slippage percentage
- All done
- Run ```python bot.py``` in terminal & register with your telegram account
- Fly
  
## File Descriptions:
- ### bot.py  
  The python bot
- ### config.py  
  The file containing the Pancake router, factory & pair ABI  
  ChainID, RPC URL & router address
- ### configs
  - #### config.json  
    User's configurations and secrets
  - #### token_list.json  
    list of tokens officially listed on pancake
  - #### personal_token_list.json  
    personal list of tokens set by users
  - #### final_token_list.json  
    list combinning personal list 
  
  
  
  





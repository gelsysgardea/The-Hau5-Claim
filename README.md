# Binance CryptoBox Wrapper
### A tool to wrap cryptoboxes from Telegram channels automatically.

## Manual:
`1` Download python from [python.org](https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe)  
`2` Install git from [git-scm.com](https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe)  
`3` Clone this repository 
```
git clone https://github.com/devbutlazy/Binance-Crypto-Box-Wrapper
```
`4` Go to`cmd.exe` and type `cd PROJECT_PATH`  
`5` Type `pip install -r requirements.txt` to install required packages  
`6` Enter the telegram API_HASH and API_ID to `source/config.py` from [here](https://my.telegram.org/auth)    
`7` Login to your [Binance Account](https://www.binance.com/uk-UA), go to [Binance Crypto Box](https://www.binance.com/uk-UA/my/wallet/account/payment/cryptobox) press F12 and go to `Network`. After that, enter a valid Crypto Box code. When entered, look for "grabV2" POST method in `Network` section. When found, go to POST method `Request Headers` and copy-paste all the neccessery information (cookie, device_info, id, etc...) from there to `source/config.py`.  
`8` Run the program
```
python main.py
```

# How it works? What are the features?

### [v2.0.0]
    - The code uses a new library for detecting messages to prevent errors (as in the past lib)
    
    - Within 1-5 seconds (for anti-detecting) the token is passed into Binance API. 

    - Custom configuration for Maximum Hour Requests in source/config.py

    - The console gives information about found crypto-tokens, and 
    if they are valid -> it give information it's about currency, amount and converts it to USDT.

    - If there is a timeout, the programm will CORRECTLY pause all the proccesses.

    - Better logging (removed logger lib), and more information about it. 

# How to create an EXE file from python code?
`1.` If you want to compile with console, run the `build-exe/CONSOLE.bat`  
`2.` If you want to compile WITHOUGHT console, run `build-exe/NO_CONSOLE.bat`

**NOTE: Cookies, and other configurations should be done in code, before running pyinstaller!** 


### (c) License: MIT-LICENSE

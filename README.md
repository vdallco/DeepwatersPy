# DeepwatersPy
Python client for swapping tokens on Deepwaters exchange


# Example
```
goerliRPCHttp = Web3.HTTPProvider("https://goerli-light.eth.linkpool.io/") # free public Goerli RPC
baseAsset = "WETH.GOERLI.5.TESTNET.PROD" # WETH
quoteAsset = "USDC.GOERLI.5.TESTNET.PROD" # USDC
swapDuration = "GOOD_TILL_CANCEL" 
swapSide = "BUY"
swapType = "LIMIT"

### Trade/swap constants ### 
price = "1250.09"
quantity = "0.0447"
############################

# TO-DO: set these before running
addr = ''
private_key = ""

dc = DeepwatersClient(goerliRPCHttp, private_key, addr)

swapResult = dc.swap(baseAsset, quoteAsset, swapSide, swapType, swapDuration, quantity, price)
print(swapResult)
```

# Example results

```
{'data': {'submitOrder': {'order': {'status': 'ACTIVE', 'venueOrderID': '....', '__typename': 'Order'}, '__typename': 'SubmitOrderResponse'}}}
```

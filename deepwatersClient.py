from eip712_structs import make_domain
from eip712_structs import EIP712Struct, String, Uint, Address
import requests
from web3 import Web3
from eth_account.messages import encode_structured_data
from eth_account import Account
import json

class DeepwatersClient:
	#### EIP712 structs ####
	domain = make_domain(name='Swap', version='1')

	class CancelOrderRequest(EIP712Struct):
		customer = Address()
		customerObjectID = String()
		orderID = String()
		nonce = Uint(256)

	class SubmitOrderRequest(EIP712Struct):
		customer = Address()
		customerObjectID = String()
		type = String()
		side = String()
		quantity = String()
		baseAssetID = String()
		quoteAssetID = String()
		price = String()
		durationType = String()
		nonce = Uint(256)

	###################################

	### Deepwaters GraphQL API constants ###
	DEEPWATERS_GRAPHQL_API_URL = "https://testnet.api.deepwaters.xyz/accounting/graphql" # for getting Customer info such as Nonce
	DEEPWATERS_GRAPHQL_SWAP_API_URL = "https://testnet.api.deepwaters.xyz/swap/graphql"

	DEEPWATERS_GRAPHQL_SUBMIT_ORDER_MUTATION = "mutation SubmitOrder($customer: String!, $type: OrderType!, $side: OrderSide!, $quantity: String!, $baseAssetID: String!, $quoteAssetID: String, $price: String!, $nonce: BigInt!, $signature: String!, $expiresAt: Time, $durationType: OrderDurationType) { submitOrder( customer: $customer type: $type side: $side quantity: $quantity baseAssetID: $baseAssetID quoteAssetID: $quoteAssetID expiresAt: $expiresAt durationType: $durationType price: $price nonce: $nonce signature: $signature ) { order { status venueOrderID __typename } __typename } }"

	DEEPWATERS_GRAPHQL_SUBMIT_ORDER_VARS = {
	  "customer": "", # populate later with self.address
	  "type": "", # populate later
	  "side": "", # populate later
	  "quantity": "", # populate later
	  "price": "", # populate later
	  "nonce": "", # populate later
	  "signature": "", # populate later
	  "baseAssetID": "", # populate later
	  "quoteAssetID": "", # populate later
	  "durationType": "" # populate later
	}

	DEEPWATERS_GRAPHQL_CUSTOMER_INFO_QUERY = "query Customer($address: String!) { customer(address: $address) { address nonce createdAt { time microsSinceEpoch __typename } modifiedAt { time microsSinceEpoch __typename } balance { assetID serviceID amount asset { assetAddress __typename } __typename } __typename } }"

	DEEPWATERS_GRAPHQL_CUSTOMER_VARS = {
	  "address": "" # populate with self.address
	}
	###############################################

	def post(self, url, query, variables): # GraphQL request
		resp = requests.post(url, json={"query": query, "variables": variables})
		return resp

	def __init__(self, httpRpcProvider, private_key, address):
		self.w3 = Web3(httpRpcProvider)
		self.address = self.w3.toChecksumAddress(address)
		self.private_key = private_key
		self.DEEPWATERS_GRAPHQL_CUSTOMER_VARS["address"] = self.address
	
	def getNonce(self):
		queryResults = self.post(self.DEEPWATERS_GRAPHQL_API_URL, self.DEEPWATERS_GRAPHQL_CUSTOMER_INFO_QUERY,  self.DEEPWATERS_GRAPHQL_CUSTOMER_VARS).json()
		return int(queryResults['data']['customer']['nonce'])

	def prepareDictForEIP712Signing(self, createOrderRequestMsg): # moves some keys to line up with Deepwaters EIP-712 message
		# We need to move the PrimaryType key to be after domain key
		newDict = {}
		primaryTypeStored = None
		for keyName in createOrderRequestMsg:
			if keyName == "primaryType":
					primaryTypeStored = createOrderRequestMsg[keyName]
			else:
					if keyName == "domain" and primaryTypeStored is not None:
							newDict[keyName] = createOrderRequestMsg[keyName]
							newDict["primaryType"] = primaryTypeStored
					else:
							newDict[keyName] = createOrderRequestMsg[keyName]
		# and move the EIP712Domain key to the end of the types list
		newestDict = {}
		newestDict["types"] = {}
		eip712DomainStored = None
		
		for keyName in newDict:
			if keyName == "types":
				for typeName in newDict[keyName]:
					if typeName == "EIP712Domain":
						eip712DomainStored = newDict['types'][typeName]
					else:
						newestDict['types'][typeName] = newDict['types'][typeName]
			else:
				newestDict[keyName] = newDict[keyName]
		
		newestDict['types']['EIP712Domain'] = eip712DomainStored
		return newestDict.copy()

	def swap(self, baseAsset, quoteAsset, side, type, duration, quantity, price):
		nextNonce = self.getNonce()

		createOrderRequest = self.SubmitOrderRequest(customer = self.address, customerObjectID = "", type = type, side = side, quantity = quantity, baseAssetID = baseAsset, quoteAssetID = quoteAsset, price = price, durationType = duration, nonce = nextNonce)
		
		createOrderRequestMsg = createOrderRequest.to_message(self.domain)
		createOrderRequestMsg = self.prepareDictForEIP712Signing(createOrderRequestMsg)
		
		createOrderSigned = encode_structured_data(text = json.dumps(createOrderRequestMsg))

		createOrderSignedMsg = Account.sign_message(signable_message = createOrderSigned, private_key = self.private_key)
		
		orderVars = self.DEEPWATERS_GRAPHQL_SUBMIT_ORDER_VARS.copy()
		orderVars["signature"] = str(createOrderSignedMsg.signature.hex())
		orderVars["nonce"] = str(nextNonce)
		orderVars["type"] = type
		orderVars["side"] = side
		orderVars["quantity"] = quantity
		orderVars["price"] = price
		orderVars["baseAssetID"] = baseAsset
		orderVars["quoteAssetID"] = quoteAsset
		orderVars["durationType"] = duration
		orderVars["customer"] = self.address

		queryResults = self.post(self.DEEPWATERS_GRAPHQL_SWAP_API_URL, self.DEEPWATERS_GRAPHQL_SUBMIT_ORDER_MUTATION, orderVars).json()
		return queryResults

## Example:

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
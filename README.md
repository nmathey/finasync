
<p align="center">
	<img src=https://github.com/nmathey/finasync/assets/20896232/cb6b9f01-ac82-49ba-863f-905ee1809237 />
</p>


# Finary Unofficial Portfolio Sync Tool

## Overview
This tool enables synchronization of your Finary portfolio with platforms that are not yet officially supported by Finary. Finary is an all-encompassing portfolio tracker, offering real-time updates on a variety of assets including precious metals, real estate, cryptocurrencies, and stocks.

If you're new to Finary, sign up with this referral link: [Join Finary](https://finary.com/referral/7aeff70ac86f973c6c1e).

## Disclaimer
:warning: Use this tool at your own risk. The author is not liable for any disruptions caused to your Finary account. :warning:

## Installation

This project uses Poetry for dependency management. To set up your environment and install the required dependencies, follow these steps:

1. **Install Poetry**  
   If you don't have Poetry installed, you can install it by following the instructions from the official Poetry documentation: [Poetry Installation](https://python-poetry.org/docs/#installation).

2. **Clone the Repository**  
   Clone the repository to your local machine using the following command:

   ```shell
   git clone https://github.com/nmathey/finasync
   cd finasync
3. **Install dependencies**
   ```shell
   poetry install
   
4. **Fill your informations**  
Copy paste the **my_info.json.tpl** file to **my_info.json** and fill your informations
   ```shell
   cp my_info.json.tpl my_info.json

5. **Run**  
`poetry run python -m finasync signin`
or
`poetry run python -m finasync me`

You may be prompted to provide a two-factor authentication code during sign-in. If so, replace `YOUR_AUTH_CODE` with the code from your authenticator app:

```bash
poetry run python -m finasync signin YOUR_AUTH_CODE
```

If you get errors about being unauthorized, you need to signin again.

## Current integrated platform

**RealT**:

Fractional and frictionless real estate investing powered by the blockchain. If you don't already have an account, here is a referral link to sign up: https://realt.co/ref/nmathey/ 
RealT is a pionner in Real Estate applied to Web3.0 and very focus on its community.

Made possible thanks to RealT Community API (https://api.realt.community/) so you need an API Key to get full RealT token details.
Here is the form to get one: [Grant API access token](https://docs.google.com/forms/d/e/1FAIpQLSf20z9fooLlq7tJTrUM4ESRlGRaqXun1wHLz5UscsF2xkdhfg/viewform)

Current working scope (tried to keep it simple for now):
- 	rentals properties only for now
- 	add/delete rentals own properties in Finary real estate rent category
- 	update properties values and monthly rent

Known limitations:
-	Gnosis network only
-	Single wallet only

Usage (once signin):
- For syncing as indvidual real estate property in "real estates" Finary category (API Key needed)
	`poetry run python -m finasync realt rent`

	To delete everything created with this command: `poetry run python -m finasync realt rent deleteall`

- For syncing every each properties in "others assets" category (API Key NOT NEEDED but less properties details)
  	`poetry run python -m finasync realt other-detailed`

	To delete everything created with this command: `poetry run python -m finasync realt other-detailed delete`

- For syncing as a single portfolio line in "others assets" category (API Key NOT NEEDED but way less details)
  	`poetry run python -m finasync realt other`

	To delete everything created with this command: `finasync realt other delete`

It will sync your RealT portfolio hosted on the blockchain to your Finary account.

## BIG thanks!

This won't be possible without:
* Finary keeping open its API ;)
* The great work of @lasconic for his Finary Unofficial API wrapper (https://github.com/lasconic/finary_uapi)
* The great work of RealT Community API (https://api.realt.community/)
* Exchange Rate API (https://www.exchangerate-api.com)
* The great idea from @MadeInPierre author of Finalynx, bringing an alternative for your Finary portfolio views and much more (https://github.com/MadeInPierre/finalynx)

## 💌 Donations

This is a personal project I have fun with on my free time. If you found it useful and wish to support my work, you can transfer any ERC20 tokens or coins to the following Ethereum/Gnosis/Polygon address are welcome: 0xEFf0d54e391C6097CdF24A3Fc450988Ebd9a91F7! 

It would give me the motivation to keep improving it further 😄 Thank you!

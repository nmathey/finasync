
<p align="center">
	<img src=https://github.com/nmathey/finasync/assets/20896232/cb6b9f01-ac82-49ba-863f-905ee1809237 />
</p>


# Finary unofficial portfolio sync tool

A simple tool to sync your Finary portfolio values with sources platforms not yet officially integrated by Finary teams.

Finary is a real time portfolio & stocks tracker. It supports precious metals, real estates, cryptos, stocks and a lot more.
If you don't already have an account, here is a referral link to sign up: https://finary.com/referral/7aeff70ac86f973c6c1e

:warning: **Use at your own risk. I'm not responsible if you trash your account**. :warning:

(I'm not a dev so forgive the quick and dirty style ;))

## BIG thanks!

This won't be possible without:
* Finary keeping open its API ;)
* The great work of @lasconic for his Finary Unofficial API wrapper (https://github.com/lasconic/finary_uapi)
* The great work of RealT Community API (https://api.realt.community/)
* Exchange Rate API (https://www.exchangerate-api.com)
* The great idea from @MadeInPierre author of Finalynx, bringing an alternative for your Finary portefolio views and much more (https://github.com/MadeInPierre/finalynx)

## Installation

Once you clone this repo, you need to install its dependencies:
```bash
cd finasync
poetry install
poetry update
```
Copy paste the my_info.json.tpl file to my_info.json and file your Finary username and password (at least), and other personal data.

Run `poetry run python -m finasync signin`

Try `poetry run python -m finasync me`

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

Usage (once signin):
	`poetry run python -m finasync realt rent`

It will sync your RealT portfolio hosted on the blockchain to your Finary account.

## 💌 Donations

This is a personal project I have fun with on my free time. If you found it useful and wish to support my work, you can transfer any ERC20 tokens or coins to the following Ethereum/Gnosis/Polygon address are welcome: 0xEFf0d54e391C6097CdF24A3Fc450988Ebd9a91F7! 

It would give me the motivation to keep improving it further 😄 Thank you!

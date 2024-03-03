import requests
import re
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
import logging

from finary_uapi.user_real_estates import (
    get_user_real_estates,
    delete_user_real_estates,
    update_user_real_estates,
    add_user_real_estates,
    add_user_real_estates_with_currency,

)

from finary_uapi.user_me import get_display_currency_code, update_display_currency_by_code

from finary_uapi.user_generic_assets import (
    get_user_generic_assets,
    add_user_generic_asset,
    update_user_generic_asset,
    delete_user_generic_asset,
)

from .constants import (
    GNOSIS_API_TOKENLIST_URI,
    GRAPH_API_TOKENLIST_URI,
    REALT_API_TOKENLIST_URI,
    REALT_OFFLINE_TOKENS_LIST,
    REALT_OFFLINE_TOKENS_LIST_FREE,
)
from .utils import convert_currency


def get_realt_token_details(realt_token_contractAdress):
    Now_Time = datetime.today()
    RealT_OfflineTokensList_Path = Path(REALT_OFFLINE_TOKENS_LIST)
    RealT_OfflineTokensList_Path.touch(exist_ok=True)
    with open(RealT_OfflineTokensList_Path) as json_file:
        try:
            RealT_OfflineTokensList = json.load(json_file)
        except JSONDecodeError:
            RealT_OfflineTokensList = {
                "info": {
                    "last_sync": str(datetime.timestamp(Now_Time - timedelta(weeks=2)))
                },
                "data": {},
            }

    # Update offlineTokensList from RealT API only if more than 1 week old
    if float(RealT_OfflineTokensList["info"]["last_sync"]) < datetime.timestamp(
        Now_Time - timedelta(weeks=1)
    ):
        MyRealT_API_Header = {
            "Accept": "*/*",
            "X-AUTH-REALT-TOKEN": os.environ["MYREALT_API_KEY"],
        }

        TokensListReq = requests.get(
            REALT_API_TOKENLIST_URI, headers=MyRealT_API_Header
        )

        TokensList = TokensListReq.json()
        logging.debug("Tokens list details from API RealT")
        logging.debug(TokensList)
        for item in TokensList:
            RealT_OfflineTokensList["data"].update(
                {
                    item.get("uuid").lower(): {
                        "fullName": item.get("fullName"),
                        "shortName": item.get("shortName"),
                        "tokenPrice": item.get("tokenPrice"),
                        "currency": item.get("currency"),
                        "rentStartDate": item.get("rentStartDate"),
                        "squareFeet": item.get("squareFeet"),
                        "totalTokens": item.get("totalTokens"),
                        "totalInvestment": item.get("totalInvestment"),
                        "grossRentMonth": item.get("grossRentMont"),
                        "propertyManagement": item.get("propertyManagement"),
                        "realtPlatform": item.get("realtPlaform"),
                        "insurance": item.get("insurance"),
                        "propertyTaxes": item.get("propertyTaxes"),
                        "propertyMaintenanceMonthly": item.get(
                            "propertyMaintenanceMonthly"
                        ),
                        "utilities": item.get("utilities"),
                        "netRentMonth": item.get("netRentMonth"),
                        "netRentMonthPerToken": item.get("netRentMonthPerToken"),
                        "coordinate": item.get("coordinate"),
                        "propertyType": item.get("propertyType"),
                        "rentalType": item.get("rentalType"),
                        "productType": item.get("productType"),
                    }
                }
            )

        RealT_OfflineTokensList["info"]["last_sync"] = str(datetime.timestamp(Now_Time))
        with open(RealT_OfflineTokensList_Path, "w") as outfile:
            json.dump(RealT_OfflineTokensList, outfile, indent=4)

    return RealT_OfflineTokensList["data"][realt_token_contractAdress]


def get_realt_rentals_finary(session: requests.Session):
    myFinary_real_estates = get_user_real_estates(session)
    myFinary_real_estates = list(
        filter(
            lambda x: re.match("^RealT -", x["description"]),
            myFinary_real_estates["result"],
        )
    )
    logging.debug("My RealT Finary portfolio")
    logging.debug(myFinary_real_estates)
    myFinary_realT = {}
    for item in myFinary_real_estates:
        contractAddress = re.findall(r"0x.+", str(item.get("description")))
        name = re.findall(r"- (.*) -", str(item.get("description")))
        myFinary_realT.update(
            {
                contractAddress[0].lower(): {
                    "name": name[0],
                    "contractAddress": contractAddress[0].lower(),
                    "finary_id": item.get("id"),
                    "category": item.get("category"),
                    "description": item.get("description"),
                    "buying_price": item.get("buying_price"),
                    "ownership_percentage": item.get("ownership_percentage"),
                }
            }
        )

    return json.dumps(myFinary_realT)


def get_realt_rentals_rmm(wallet_address):    
    if not GRAPH_API_TOKENLIST_URI:
        logging.error("The GRAPH_API_TOKENLIST_URI environment variable is not set or is empty.")
        return []

    query = """
    query getUserBalance($userAddress: String!) {
        userRealTokens(where: {user: $userAddress}, first: 1000) {
            id
            amount
            token {
                symbol
                address
            }
        }
    }
    """

    payload = {
        "query": query.strip(),
        "variables": {"userAddress": wallet_address}
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(GRAPH_API_TOKENLIST_URI, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        response_json = response.json()
        if 'errors' in response_json:
            print('GraphQL errors:', response_json['errors'])
            return []

        return response_json.get('data', {}).get('userRealTokens', [])

    except requests.exceptions.HTTPError as e:
        print('HTTP request failed:', e)
    except requests.exceptions.RequestException as e:
        print('Request exception:', e)
    except json.JSONDecodeError as e:
        print('JSON decode error:', e)

    return []

def get_realt_rentals_blockchain(wallet_address):
    realT_rentals_rmm = get_realt_rentals_rmm(wallet_address)
    for token_info in realT_rentals_rmm:
        amount_in_ether = int(token_info['amount']) / 1e18
        log_message = f"RMM Property found: {token_info['token']['symbol']}, Amount: {amount_in_ether} tokens"
        print(log_message)

    myWallet = json.loads(requests.get(GNOSIS_API_TOKENLIST_URI + wallet_address).text)
    myRealT_rentals = {}
    logging.debug("My wallet details")
    logging.debug(myWallet)
    for item in myWallet["result"]:
        if re.match(r"^REALTOKEN", str(item.get("symbol")), re.IGNORECASE):
            logging.debug("Updating RealT Token to Finary: " + item["symbol"])
            myRealT_rentals.update(
                {
                    item["contractAddress"].lower(): {
                        "name": item["symbol"],
                        "balance": float(item["balance"])
                        / pow(10, int(item["decimals"])),
                        "contractAddress": item["contractAddress"].lower(),
                    }
                }
            )
        elif re.match(r"^armmREALT", str(item.get("symbol"))):
            time.sleep(0.2)
            original_contract_address = requests.get(
                GNOSIS_API_TOKENLIST_URI + item["contractAddress"]
            ).json()
            original_contract_address = list(
                filter(
                    lambda x: re.match("^REALTOKEN", x["symbol"]),
                    original_contract_address["result"],
                )
            )
            original_contract_address = str(
                original_contract_address[0]["contractAddress"]
            )
            logging.debug("Updating armm RealT Token to Finary: " + item["symbol"])
            myRealT_rentals.update(
                {
                    original_contract_address.lower(): {
                        "name": item["symbol"],
                        "balance": float(item["balance"])
                        / pow(10, int(item["decimals"])),
                        "contractAddress": original_contract_address.lower(),
                    }
                }
            )
    logging.debug("My RealT portfolio from the blockchain")
    logging.debug(myRealT_rentals)

    return json.dumps(myRealT_rentals)


def get_building_type(realT_propertyType):
    # building type: house, building, apartment, land, commercial, parking_box, or other
    # propertyType from RealT -> 1 = Single Family | 2 = Multi Family | 3 = Duplex | 4 = Condominium | 6 = Mixed-Used | 8 = Quadplex | 9 = Commercial |10 = SFR Portfolio
    building_type = "other"
    if realT_propertyType == 1:
        building_type = "house"
    elif realT_propertyType == 2 or realT_propertyType == 3 or realT_propertyType == 8:
        building_type = "building"
    elif realT_propertyType == 4 or realT_propertyType == 9:
        building_type = "commercial"

    return building_type


def sync_realt_rent(session: requests.Session, wallet_address):
    # Get current Finary RealT rent portfolio
    myFinary_realT = json.loads(get_realt_rentals_finary(session))

    # Get current RealT rent from wallet
    myRealT_rentals = json.loads(get_realt_rentals_blockchain(wallet_address))

    # If finary RealT rentals not in RealT wallet then delete otherwise update
    myFinary_displaycurrency = get_display_currency_code(session)
    logging.debug("UI Display currency: " + myFinary_displaycurrency)
    for key in myFinary_realT:
        if key not in myRealT_rentals:
            delete_user_real_estates(session, myFinary_realT[key]["finary_id"])
            logging.info("Deleting " + myFinary_realT[key]["description"])
        else:
            token_details = get_realt_token_details(key)

            # Handling currency
            logging.debug("UI Display currency: " + myFinary_displaycurrency)
            if token_details["currency"] == myFinary_displaycurrency:
                user_estimated_value = (
                    token_details["totalTokens"] * token_details["tokenPrice"]
                )
                monthly_rent = token_details["netRentMonth"]
            elif (
                token_details["currency"] == "EUR"
                or "USD"
                or "SGD"
                or "CHF"
                or "GBP"
                or "CAD"
            ):
                user_estimated_value = (
                    token_details["totalTokens"] * token_details["tokenPrice"]
                )
                monthly_rent = token_details["netRentMonth"]
            else:
                user_estimated_value = token_details["totalTokens"] * convert_currency(
                    token_details["tokenPrice"],
                    token_details["currency"],
                    myFinary_displaycurrency,
                )
                monthly_rent = convert_currency(
                    token_details["netRentMonth"],
                    token_details["currency"],
                    myFinary_displaycurrency,
                )

            ownership_percentage = round(
                (myRealT_rentals[key]["balance"] / token_details["totalTokens"]) * 100,
                4,
            )

            logging.info(
                "updating "
                + myFinary_realT[key]["description"]
                + " balance to "
                + str(myRealT_rentals[key]["balance"])
                + " / "
                + str(token_details["totalTokens"])
                + " ~ "
                + str(ownership_percentage)
            )
            update_user_real_estates(
                session,
                "rent",  # category
                myFinary_realT[key]["finary_id"],  # asset_id
                user_estimated_value,  # user_estimated_value
                myFinary_realT[key]["description"],  # description
                (myFinary_realT[key]["buying_price"]),  # buying_price
                ownership_percentage,  # ownership_percentage = number of token own / total number of token
                monthly_rent,  # monthly_rent (total)
            )

    # If Realt token in wallet not in Finary then add
    for key in myRealT_rentals:
        if key not in myFinary_realT:
            token_details = get_realt_token_details(key)

            # Handling null value recieved from API
            if token_details["squareFeet"] is not None:
                squareFeet = float(token_details["squareFeet"])
            else:
                squareFeet = 1.0

            category = "rent"  #'rent' for RealT rental property

            logging.info(
                    "add "
                    + str(myRealT_rentals[key]["balance"])
                    + " "
                    + token_details["shortName"]
                    + " @ "
                    + str(token_details["tokenPrice"])
                )
            # Handling currency
            if token_details["currency"] == myFinary_displaycurrency:
                # if property currency same as display currency
                logging.debug("Property with same currency as display currency : just add it")
                add_user_real_estates(
                    session,
                    category,
                    (
                        token_details["fullName"].replace(" Holdings", "")
                    ),  # address, #use to get the place ID from address
                    (
                        token_details["totalTokens"] * token_details["tokenPrice"]
                    ),  # user_estimated_value
                    "RealT - " + token_details["fullName"] + " - " + key,  # description
                    round(
                        (squareFeet * 0.092903), 0
                    ),  # surface in sqm (RealT provide in sqft)
                    (
                        token_details["totalTokens"] * token_details["tokenPrice"]
                    ),  # using market value at the time of the property addition in Finary portfolio (might ignore previous revaluation)
                    get_building_type(token_details["propertyType"]),
                    (
                        (myRealT_rentals[key]["balance"] / token_details["totalTokens"])
                        * 100
                    ),  # ownership percentage
                    0,  # monthy charges (total) (mandatory for rent category) - set to zero to keep it simple for now
                    token_details[
                        "netRentMonth"
                    ],  # monthly rent (total) (mandatory for rent category)
                    0,  # yearly taxes (mandatory for rent category) - set to zero to keep it simple for now
                    (
                        "annual"
                        if token_details["rentalType"] == "long_term"
                        else "seasonal"
                    ),  # rental period: annual (=long_term) or seasonal (=short_term) (mandatory if rent category)
                    "nue",  # rental type: "nue" for RealT rental property (mandatory for rent category)
                )
            elif (
                token_details["currency"] == "EUR"
                or "USD"
                or "SGD"
                or "CHF"
                or "GBP"
                or "CAD"
            ):
                # if property currency different than display currency but Finary compatible
                logging.debug("Property with compatible Finary currency: swicthing display currency")
                add_user_real_estates_with_currency(
                    session,
                    category,
                    (
                        token_details["fullName"].replace(" Holdings", "")
                    ),  # address used to get the place ID
                    token_details["currency"],  # property currency code
                    (
                        token_details["totalTokens"] * token_details["tokenPrice"]
                    ),  # user_estimated_value
                    "RealT - " + token_details["fullName"] + " - " + key,  # description
                    round(
                        (squareFeet * 0.092903), 0
                    ),  # surface in sqm (RealT provide in sqft)
                    (
                        token_details["totalTokens"] * token_details["tokenPrice"]
                    ),  # buying price using market value at the time of the property addition in Finary portfolio (might ignore previous revaluation)
                    get_building_type(token_details["propertyType"]),
                    (
                        (myRealT_rentals[key]["balance"] / token_details["totalTokens"])
                        * 100
                    ),  # ownership percentage
                    0,  # monthy charges (total) in Euro (mandatory for rent category) - set to zero to keep it simple for now
                    token_details[
                        "netRentMonth"
                    ],  # monthly rent (total) (mandatory for rent category)
                    0,  # yearly taxes in Euro (mandatory for rent category) - set to zero to keep it simple for now
                    (
                        "annual"
                        if token_details["rentalType"] == "long_term"
                        else "seasonal"
                    ),  # rental period: annual (=long_term) or seasonal (=short_term) (mandatory if rent category)
                    "nue",  # rental type: "nue" for RealT rental property (mandatory for rent category)
                )
                time.sleep(0.2)
            else:
                # if property currency not Finary compatible then convert in display currency
                logging.debug("Property with uncompatible Finary currency: converting in display currency")
                add_user_real_estates(
                    session,
                    category,
                    (
                        token_details["fullName"].replace(" Holdings", "")
                    ),  # address, #use to get the place ID from address
                    (
                        token_details["totalTokens"]
                        * convert_currency(
                            token_details["tokenPrice"],
                            token_details["currency"],
                            myFinary_displaycurrency,
                        )
                    ),  # user_estimated_value (in EUR) = current token value * total number of token
                    "RealT - " + token_details["fullName"] + " - " + key,  # description
                    round(
                        (squareFeet * 0.092903), 0
                    ),  # surface in sqm (RealT provide in sqft)
                    (
                        token_details["totalTokens"]
                        * convert_currency(
                            token_details["tokenPrice"],
                            token_details["currency"],
                            myFinary_displaycurrency,
                        )
                    ),  # using market value at the time of the property addition in Finary portfolio (might ignore previous revaluation)
                    get_building_type(token_details["propertyType"]),
                    (
                        (myRealT_rentals[key]["balance"] / token_details["totalTokens"])
                        * 100
                    ),  # ownership percentage
                    0,  # monthy charges (total) in Euro (mandatory for rent category) - set to zero to keep it simple for now
                    (
                        convert_currency(
                            token_details["netRentMonth"],
                            token_details["currency"],
                            myFinary_displaycurrency,
                        )
                    ),  # monthly rent (total) in Euro (mandatory for rent category)
                    0,  # yearly taxes in Euro (mandatory for rent category) - set to zero to keep it simple for now
                    (
                        "annual"
                        if token_details["rentalType"] == "long_term"
                        else "seasonal"
                    ),  # rental period: annual (=long_term) or seasonal (=short_term) (mandatory if rent category)
                    "nue",  # rental type: "nue" for RealT rental property (mandatory for rent category)
                )

    return 0


def delete_all_realt_rentals_finary(session: requests.Session):
    # Get current Finary RealT rent portfolio
    myFinary_realT = json.loads(get_realt_rentals_finary(session))
    logging.debug("My current RealT portfolio in Finary")
    logging.debug(myFinary_realT)
    for key in myFinary_realT:
        delete_user_real_estates(session, myFinary_realT[key]["finary_id"])
        logging.info("Deleting " + myFinary_realT[key]["description"])

    return 0

def get_realtportfolio_other_finary(session: requests.Session):
    myFinary_realt_portfolio = get_user_generic_assets(session)
    myFinary_realt_portfolio = list(
        filter(
            lambda x: re.match("^RealT Portfolio", x["name"]),
            myFinary_realt_portfolio["result"],
        )
    )
    logging.debug("My RealT Finary portfolio")
    logging.debug(myFinary_realt_portfolio)
    
    if myFinary_realt_portfolio:
        return myFinary_realt_portfolio[0]
    else:
        return None

def get_realt_token_details_free(realt_token_contractAdress):
    Now_Time = datetime.today()
    RealT_OfflineTokensList_Path = Path(REALT_OFFLINE_TOKENS_LIST_FREE)
    RealT_OfflineTokensList_Path.touch(exist_ok=True)
    with open(RealT_OfflineTokensList_Path) as json_file:
        try:
            RealT_OfflineTokensList = json.load(json_file)
        except JSONDecodeError:
            RealT_OfflineTokensList = {
                "info": {
                    "last_sync": str(datetime.timestamp(Now_Time - timedelta(weeks=2)))
                },
                "data": {},
            }

    # Update offlineTokensList from RealT API only if more than 1 week old
    if float(RealT_OfflineTokensList["info"]["last_sync"]) < datetime.timestamp(
        Now_Time - timedelta(weeks=1)
    ):
        MyRealT_API_Header = {
            "Accept": "*/*",
        }

        TokensListReq = requests.get(
            REALT_API_TOKENLIST_URI, headers=MyRealT_API_Header
        )

        TokensList = TokensListReq.json()
        logging.debug("Tokens list details from API RealT - Free call")
        logging.debug(TokensList)
        for item in TokensList:
            RealT_OfflineTokensList["data"].update(
                {
                    item.get("uuid").lower(): {
                        "fullName": item.get("fullName"),
                        "shortName": item.get("shortName"),
                        "tokenPrice": item.get("tokenPrice"),
                        "currency": item.get("currency"),
                        "productType": item.get("productType"),
                    }
                }
            )

        RealT_OfflineTokensList["info"]["last_sync"] = str(datetime.timestamp(Now_Time))
        with open(RealT_OfflineTokensList_Path, "w") as outfile:
            json.dump(RealT_OfflineTokensList, outfile, indent=4)

    return RealT_OfflineTokensList["data"][realt_token_contractAdress]

def get_realtportfolio_value(wallet_address):
    myRealT_rentals = json.loads(get_realt_rentals_blockchain(wallet_address))

    myRealT_portfolio_value = 0
    for key in myRealT_rentals:
        token_details_free = get_realt_token_details_free(key)
        myRealT_portfolio_value = myRealT_portfolio_value + myRealT_rentals[key]['balance'] * token_details_free['tokenPrice']

    return myRealT_portfolio_value

def sync_realtportfolio_other(session: requests.Session, wallet_address):

    # Get current RealT Portfolio from Finary
    myFinary_RealTPortfolio = get_realtportfolio_other_finary(session)
    myRealT_Portfolio_value = get_realtportfolio_value(wallet_address)
    
    if myFinary_RealTPortfolio is not None:
        logging.info("Updating RealtT Portfolio in other assets id " + str(myFinary_RealTPortfolio['id']))
        update_user_generic_asset(
            session,
            myFinary_RealTPortfolio['id'],
            myFinary_RealTPortfolio['name'],
            myFinary_RealTPortfolio['category'],
            1,
            myFinary_RealTPortfolio['buying_price'],
            myRealT_Portfolio_value
        )
    else:
        myFinary_displaycurrency = get_display_currency_code(session)
        if myFinary_displaycurrency != "USD":
            update_display_currency_by_code(session, "USD")
            add_user_generic_asset(session, "RealT Portfolio", "other", 1 , myRealT_Portfolio_value , myRealT_Portfolio_value)
            time.sleep(0.02)
            update_display_currency_by_code(session, myFinary_displaycurrency)
        else:
            add_user_generic_asset(session, "RealT Portfolio", "other", 1 , myRealT_Portfolio_value , myRealT_Portfolio_value)
        logging.info("Adding RealtT Portfolio in other assets category as one line for a value of " + str(myRealT_Portfolio_value))

    return 0

def delete_realtportfolio_other_finary(session: requests.Session):
    myFinary_RealTPortfolio = get_realtportfolio_other_finary(session)
    delete_user_generic_asset(session, myFinary_RealTPortfolio['id'])
    logging.info("Deleting " + str(myFinary_RealTPortfolio['id']))

    return 0

def get_realt_others_finary(session: requests.Session):
    myFinary_realT_generic_assets = get_user_generic_assets(session)
    myFinary_realT_generic_assets = list(
        filter(
            lambda x: re.match("^RealT -", x["name"]),
            myFinary_realT_generic_assets["result"],
        )
    )
    logging.debug("My RealT Finary portfolio")
    logging.debug(myFinary_realT_generic_assets)
    myFinary_realT_others = {}
    for item in myFinary_realT_generic_assets:
        contractAddress = re.findall(r"0x.+", str(item.get("name")))
        name = re.findall(r"- (.*) -", str(item.get("name")))
        myFinary_realT_others.update(
            {
                contractAddress[0].lower(): {
                    "name": name[0],
                    "contractAddress": contractAddress[0].lower(),
                    "finary_id": item.get("id"),
                    "buying_price": item.get("buying_price"),
                    "balance": item.get("quantity"),
                }
            }
        )

    return json.dumps(myFinary_realT_others)

## A TESTER ##
def sync_realtproperties_other(session: requests.Session, wallet_address):
    # Get current Finary RealT others assets portfolio
    myFinary_realT_others = json.loads(get_realt_others_finary(session))

    # Get current RealT rent from wallet
    myRealT_rentals = json.loads(get_realt_rentals_blockchain(wallet_address))

    # If finary RealT rentals not in RealT wallet then delete otherwise update
    myFinary_displaycurrency = get_display_currency_code(session)
    logging.debug("UI Display currency: " + myFinary_displaycurrency)
    for key in myFinary_realT_others:
        if key not in myRealT_rentals:
            delete_user_generic_asset(session, myFinary_realT_others[key]["finary_id"])
            logging.info("Deleting " + myFinary_realT_others[key]["name"])
        else:
            token_details_free = get_realt_token_details_free(key)

            # Handling currency
            logging.debug("UI Display currency: " + myFinary_displaycurrency)
            logging.info(
                "updating "
                + myFinary_realT_others[key]["name"]
                + " balance to "
                + str(myRealT_rentals[key]["balance"])
            )
            update_user_generic_asset(
                session,
                myFinary_realT_others[key]['finary_id'],
                "RealT - " + token_details_free["fullName"] + " - " + key,
                "other",
                myRealT_rentals[key]["balance"],
                myFinary_realT_others[key]['buying_price'],
                token_details_free["tokenPrice"]
            )

    # If Realt token in wallet not in Finary then add
    myCurrent_displaycurrency = myFinary_displaycurrency
    for key in myRealT_rentals:
        if key not in myFinary_realT_others:
            token_details_free = get_realt_token_details_free(key)

            logging.info(
                    "add "
                    + str(myRealT_rentals[key]["balance"])
                    + " "
                    + token_details_free["shortName"]
                    + " @ "
                    + str(token_details_free["tokenPrice"])
                )
            # Handling currency
            if token_details_free["currency"] == myCurrent_displaycurrency:
                # if property currency same as display currency
                logging.debug("Property with same currency as display currency : just add it")
                add_user_generic_asset(
                    session,
                    "RealT - " + token_details_free["fullName"] + " - " + key,
                    "other",
                    myRealT_rentals[key]["balance"],
                    token_details_free["tokenPrice"],
                    token_details_free["tokenPrice"]
                )
            elif (
                token_details_free["currency"] == "EUR"
                or "USD"
                or "SGD"
                or "CHF"
                or "GBP"
                or "CAD"
            ):
                # if property currency different than display currency but Finary compatible
                logging.debug("Property with compatible Finary currency: swicthing display currency")
                if myCurrent_displaycurrency != token_details_free["currency"]:
                    update_display_currency_by_code(session, token_details_free["currency"])
                    myCurrent_displaycurrency = token_details_free["currency"]
                    time.sleep(0.2)
                    logging.debug("adding the property")
                    add_user_generic_asset(
                        session,
                        "RealT - " + token_details_free["fullName"] + " - " + key,
                        "other",
                        myRealT_rentals[key]["balance"],
                        token_details_free["tokenPrice"],
                        token_details_free["tokenPrice"]
                    )    
            else:
                # if property currency not compatible with Finary then convert in display currency
                logging.debug("Property currency not compatible with Finary: converting in display currency")
                add_user_generic_asset(
                        session,
                        "RealT - " + token_details_free["fullName"] + " - " + key,
                        "other",
                        myRealT_rentals[key]["balance"],
                        convert_currency(
                            token_details_free["tokenPrice"],
                            token_details_fre["currency"],
                            myFinary_displaycurrency,
                        ),
                        convert_currency(
                            token_details_free["tokenPrice"],
                            token_details_free["currency"],
                            myFinary_displaycurrency,
                        )
                    )
    time.sleep(0.2)
    logging.debug("Switching currency back")
    update_display_currency_by_code(session, myFinary_displaycurrency)

    return 0

def delete_realtproperties_other_finary(session: requests.Session):
    myFinary_realT_others = json.loads(get_realt_others_finary(session))
    for key in myFinary_realT_others:
        delete_user_generic_asset(session, myFinary_realT_others[key]["finary_id"])
        print("Deleting " + myFinary_realT_others[key]["name"])

    return 0

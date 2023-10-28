import requests
import re
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError

from finary_uapi.constants import API_ROOT
from finary_uapi.user_real_estates import (
    get_user_real_estates,
    delete_user_real_estates,
    update_user_real_estates,
    add_user_real_estates,
)

from .constants import (
    GNOSIS_API_TOKENLIST_URI,
    REALT_API_TOKENLIST_URI,
    REALT_OFFLINE_TOKENS_LIST,
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
        for item in TokensList:
            RealT_OfflineTokensList["data"].update(
                {
                    item.get("uuid").lower(): {
                        "fullName": item.get("fullName"),
                        "shortName": item.get("shortName"),
                        "tokenPrice": item.get("tokenPrice"),
                        "netRentMonthPerToken": item.get("netRentMonthPerToken"),
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
                        "rentStartDate": item.get("rentStartDate"),
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


def get_realt_rentals_blockchain(wallet_address):
    myWallet = json.loads(requests.get(GNOSIS_API_TOKENLIST_URI + wallet_address).text)
    myRealT_rentals = {}
    for item in myWallet["result"]:
        if re.match(r"^REALTOKEN", str(item.get("symbol")), re.IGNORECASE):
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
            time.sleep(1)
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
    for key in myFinary_realT:
        if key not in myRealT_rentals:
            delete_user_real_estates(session, myFinary_realT[key]["finary_id"])
        else:
            token_details = get_realt_token_details(key)
            update_user_real_estates(
                session,
                myFinary_realT[key]["finary_id"],  # asset_id
                "rent",  # category
                (
                    token_details["totalTokens"]
                    * convert_currency(
                        token_details["tokenPrice"], token_details["currency"], "EUR"
                    )
                ),  # user_estimated_value (in EUR) = current token value * total number of token
                myFinary_realT[key]["description"],  # description
                (myFinary_realT[key]["buying_price"]),  # buying_price
                (
                    (myRealT_rentals[key]["balance"] / token_details["totalTokens"])
                    * 100
                ),  # ownership_percentage = number of token own / total number of token
                (
                    convert_currency(
                        token_details["netRentMonth"], token_details["currency"], "EUR"
                    )
                ),  # monthly_rent (total)
            )
            print(token_details)

    # If Realt token in wallet not in Finary then add
    for key in myRealT_rentals:
        if key not in myFinary_realT:
            token_details = get_realt_token_details(key)
            category = "rent"  #'rent' for RealT rental property
            add_user_real_estates(
                session,
                category,
                (
                    token_details["fullName"].replace(" Holdings", "")
                ),  # address, #use to get the place ID from address
                (
                    token_details["totalTokens"]
                    * convert_currency(
                        token_details["tokenPrice"], token_details["currency"], "EUR"
                    )
                ),  # user_estimated_value (in EUR) = current token value * total number of token
                "RealT - " + token_details["fullName"] + " - " + key,  # description
                round(
                    (token_details["squareFeet"] * 0.092903), 0
                ),  # surface in sqm (RealT provide in sqft)
                (
                    token_details["totalTokens"]
                    * convert_currency(
                        token_details["tokenPrice"], token_details["currency"], "EUR"
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
                        token_details["netRentMonth"], token_details["currency"], "EUR"
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
        for key in myFinary_realT:
            delete_user_real_estates(session, myFinary_realT[key]["finary_id"])

    return 0

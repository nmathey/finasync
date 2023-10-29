"""
Finary command line
Usage:
    finasync signin [MFA_CODE]
    finasync me
    finasync realt rent
    finasync realt rent deleteall
"""
import json
import sys
import os

from docopt import docopt

from finary_uapi.auth import prepare_session
from finary_uapi.signin import signin
from finary_uapi.user_me import get_user_me

from .realt import sync_realt_rent, delete_all_realt_rentals_finary


def main() -> int:  # pragma: nocover
    """Main entry point."""
    import logging

    logging.basicConfig(level=logging.INFO)

    # load secrets from my_info.json to os.env
    myInfo_file = open("my_info.json", "r")
    myInfo = json.load(myInfo_file)
    os.environ["FINARY_EMAIL"] = myInfo["FINARY_EMAIL"]
    os.environ["FINARY_PASSWORD"] = myInfo["FINARY_PASSWORD"]
    os.environ["MYREALT_API_KEY"] = myInfo["MYREALT_API_KEY"]
    os.environ["MYREALT_WALLET_ADDRESS"] = myInfo["MYREALT_WALLET_ADDRESS"]

    args = docopt(__doc__)
    result = ""
    if args["signin"]:
        result = signin(args["MFA_CODE"])
    else:
        session = prepare_session()
        if args["me"]:
            result = get_user_me(session)
        elif args["realt"]:
            if args["rent"]:
                if args["deleteall"]:
                    result = delete_all_realt_rentals_finary(session)
                else:
                    result = sync_realt_rent(
                        session, os.environ["MYREALT_WALLET_ADDRESS"]
                    )
    if result:
        print(json.dumps(result, indent=4))

    return 0


if __name__ == "__main__":  # pragma: nocover
    sys.exit(main())

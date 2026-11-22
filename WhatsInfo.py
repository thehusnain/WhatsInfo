import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import phonenumbers
import requests
from colorama import Fore, Style, init
from dotenv import load_dotenv

init(autoreset=True)

NETWORK_IDENTIFIER_KEYS = {"ip", "last_ip", "connected_ip"}


def redact_network_identifiers(data):
    if isinstance(data, dict):
        return {
            key: "[redacted]"
            if isinstance(key, str) and key.lower() in NETWORK_IDENTIFIER_KEYS
            else redact_network_identifiers(value)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [redact_network_identifiers(item) for item in data]
    return data


def save_report(report_path, phone_number, api_host, data, show_network_identifiers=False):
    report_data = data if show_network_identifiers else redact_network_identifiers(data)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phone_number": phone_number,
        "provider": api_host,
        "data": report_data,
    }
    destination = Path(report_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def print_colored_json(data, level=0, show_network_identifiers=False):
    indent = "    " * level
    if isinstance(data, dict):
        for key, value in data.items():
            if not show_network_identifiers and key.lower() in NETWORK_IDENTIFIER_KEYS:
                value = "[redacted]"
            if isinstance(value, (dict, list)):
                print(f"{indent}{Fore.CYAN}{key}{Style.RESET_ALL}:")
                print_colored_json(value, level + 1, show_network_identifiers)
            else:
                print(f"{indent}{Fore.CYAN}{key}{Style.RESET_ALL}: {Fore.YELLOW}{value}{Style.RESET_ALL}")
    elif isinstance(data, list):
        for index, item in enumerate(data):
            print(f"{indent}{Fore.CYAN}[{index}]{Style.RESET_ALL}:")
            print_colored_json(item, level + 1, show_network_identifiers)
    else:
        print(f"{indent}{Fore.YELLOW}{data}{Style.RESET_ALL}")


def validate_phone_number(phone_number):
    normalized = phone_number.strip()
    if normalized.startswith("00"):
        normalized = "+" + normalized[2:]
    elif not normalized.startswith("+"):
        normalized = "+" + normalized

    try:
        parsed_number = phonenumbers.parse(normalized, None)
    except phonenumbers.NumberParseException:
        return None

    if not phonenumbers.is_valid_number(parsed_number):
        return None
    return phonenumbers.format_number(
        parsed_number, phonenumbers.PhoneNumberFormat.E164
    )


def get_whatsapp_number_info(phone_number, api_key, api_host, show_network_identifiers=False):
    url_number = phone_number.removeprefix("+")
    url = f"https://{api_host}/number/{url_number}"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        print(f"{Fore.RED}Request timed out. The API might be slow or unavailable.{Style.RESET_ALL}")
        return None
    except requests.exceptions.HTTPError:
        print(f"{Fore.RED}API request failed with HTTP {response.status_code}.{Style.RESET_ALL}")
        if response.status_code in (401, 403):
            print(f"{Fore.YELLOW}Check your RapidAPI key, host, and subscription.{Style.RESET_ALL}")
        return None
    except requests.exceptions.RequestException as error:
        print(f"{Fore.RED}Request failed: {error}{Style.RESET_ALL}")
        return None
    except ValueError:
        print(f"{Fore.RED}The API returned invalid JSON.{Style.RESET_ALL}")
        return None

    print(f"\n{Fore.GREEN}WhatsApp Information:{Style.RESET_ALL}")
    print_colored_json(data, show_network_identifiers=show_network_identifiers)
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Look up WhatsApp information for one international phone number."
    )
    parser.add_argument(
        "--show-network-identifiers",
        action="store_true",
        help="show IP-like fields returned by the provider (hidden by default)",
    )
    parser.add_argument(
        "--save-report",
        metavar="PATH",
        help="save this lookup's JSON report locally (IP-like fields are redacted by default)",
    )
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST")
    if not api_key or not api_host:
        print(
            f"{Fore.RED}Missing RAPIDAPI_KEY or RAPIDAPI_HOST. "
            "Set them in your local .env file.{Style.RESET_ALL}"
        )
        return 1

    print(Fore.GREEN + """
     __i
    |---|    
    |[_]|    
    |:::|    
    |:::|    
    `\\   \\   
      \\_=_\\ 
    WhatsApp Number Information Lookup
    """ + Style.RESET_ALL)

    number = input("Enter the phone number (with country code): ")

    validated_number = validate_phone_number(number)
    if not validated_number:
        print(f"{Fore.RED}Invalid number. Enter a valid international number with country code.{Style.RESET_ALL}")
        return 1

    print(f"{Fore.CYAN}Checking number: {validated_number}{Style.RESET_ALL}")

    print(
        f"{Fore.YELLOW}This sends the number to the configured RapidAPI provider. "
        "Only continue if you have permission to look it up.{Style.RESET_ALL}"
    )
    if input("Continue? [y/N]: ").strip().lower() not in ("y", "yes"):
        print("Lookup cancelled.")
        return 0

    data = get_whatsapp_number_info(
        validated_number,
        api_key,
        api_host,
        show_network_identifiers=args.show_network_identifiers,
    )
    if data is None:
        return 1

    if args.save_report:
        try:
            save_report(
                args.save_report,
                validated_number,
                api_host,
                data,
                show_network_identifiers=args.show_network_identifiers,
            )
        except OSError as error:
            print(f"{Fore.RED}Could not save report: {error}{Style.RESET_ALL}")
            return 1
        print(f"{Fore.GREEN}Report saved to {args.save_report}{Style.RESET_ALL}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
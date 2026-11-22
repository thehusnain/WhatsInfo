# WhatsInfo

WhatsInfo is a small command-line client for the third-party WhatsApp Data API on RapidAPI. It does not connect to WhatsApp directly. Use it only for numbers you are authorized to check, and review the provider's privacy policy and terms before submitting data.

## Setup

Get a RapidAPI key and host for the [WhatsApp Data API](https://rapidapi.com/airaudoeduardo/api/whatsapp-data1). Copy `.env.example` to `.env` and add your credentials:

```sh
cp .env.example .env
```

Install dependencies and run:

```sh
python3 -m pip install -r requirements.txt
python3 WhatsInfo.py
```

The app validates and normalizes international numbers to E.164, asks for confirmation before sending a number to RapidAPI, and hides IP-like fields in the response by default. To display those fields, run:

```sh
python3 WhatsInfo.py --show-network-identifiers
```

You can optionally save a local JSON report with the normalized number, provider, timestamp, and API response:

```sh
python3 WhatsInfo.py --save-report reports/lookup.json
```

IP-like fields are redacted in saved reports by default as well. If you also pass `--show-network-identifiers`, those fields will be included in the report.

The API key is read from the local `.env` file and must never be committed. If a key has already been pushed to a remote repository, revoke or rotate it in RapidAPI; adding `.env` to `.gitignore` does not remove it from Git history.

## Tests

```sh
python3 -m unittest discover -s tests
```

## Support

Questions, bugs, or suggestions: huxnain.cs@gmail.com

See [LICENSE](LICENSE) for license information.

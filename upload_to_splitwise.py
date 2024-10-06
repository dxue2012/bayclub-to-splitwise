import argparse
import json
import logging
import pprint
import sys

import pandas as pd
import pandas.api.types as ptypes

from bayclub_statement_parser import Bayclub_statement_parser
from splitwise_client import Splitwise_client

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

UNKNOWN_MEMBER_KEY = "Unknown"
ALL_MEMBERS_KEY = "All"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a bayclub statement and upload charges to splitwise"
    )

    # Two positional arguments for file paths
    parser.add_argument("--config", type=str,
                        required=True, help="The path to the config JSON.")
    parser.add_argument(
        "--statement-pdf", type=str, required=True, help="The path to the statement PDF."
    )

    # Optional boolean flag (by default False, True if present)
    parser.add_argument(
        "--upload-to-splitwise",
        action="store_true",
        help="Uploads to splitwise if specified",
    )

    return parser.parse_args()


def process_statement(statement: pd.DataFrame, group_id: str, payer_name: str, name_to_id: dict) -> list:
    """Process the statement and add expenses using Splitwise user IDs."""

    # Get the payer's user ID from the group member mapping
    payer_user_id = name_to_id.get(payer_name)

    if not payer_user_id:
        raise ValueError(
            f"Error: Payer '{payer_name}' not found in the group!")

    statement.columns = statement.columns.str.lower()
    if not ptypes.is_numeric_dtype(statement['amount']):
        statement['amount'] = pd.to_numeric(
            statement['amount'].str.replace(',', ''), errors='coerce')

    # Loop through each row and process the data
    expenses = []
    for _, row in statement.iterrows():
        date = row.date
        cost = row.amount
        description = row.description
        member = row.assigned_member
        reason = row.reason

        details = reason

        # Skip rows where the cost is negative or NaN
        if pd.isna(cost) or cost <= 0:
            logging.warning(f"Skipping row with invalid cost: {row}")
            continue

        # Parse the date into the required YYYY-MM-DD format
        try:
            date_str = pd.to_datetime(date).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            logging.error(f"Error: Invalid date format for row: {row}")
            continue

        user_shares = {}

        if member == ALL_MEMBERS_KEY:
            # Split equally among all members (except "Unknown")
            actual_members = {
                k: v for k, v in name_to_id.items() if k != UNKNOWN_MEMBER_KEY}
            num_members = len(actual_members)

            # Calculate each member's share, rounded to 2 decimals
            # because that's SplitWise's precision
            owed_amount_per_member = round(cost / num_members, 2)

            rounded_cost = owed_amount_per_member * num_members

            if cost != rounded_cost:
                details = f"{details}, cost rounded so that individual amounts add up to the total"
                cost = rounded_cost

            # Assign shares (Payer pays, everyone owes equally)
            for member_name, member_id in actual_members.items():
                paid = cost if member_name == payer_name else 0
                user_shares[member_id] = {
                    "paid": paid, "owed": owed_amount_per_member}

        else:
            # Regular case with known members
            # Use the payer's user ID and the other member's ID (retrieved from name_to_id)
            other_member_id = name_to_id.get(member)
            if not other_member_id:
                logging.error(
                    f"Error: Could not find member '{member}' in the group. Known members are {name_to_id}"
                )
                continue

            user_shares = {
                # Payer pays the full amount
                payer_user_id: {"paid": cost, "owed": 0},
                other_member_id: {
                    "paid": 0,
                    "owed": cost,
                },  # Other member owes the full cost
            }

        expenses.append((cost, description, date_str,
                        group_id, user_shares, details))

    return expenses


if __name__ == "__main__":
    args = parse_args()

    with open("secrets.json", "r") as file:
        secrets = json.load(file)

    splitwise_client = Splitwise_client(secrets)

    # Load the config JSON to get the group_id and payer name
    with open(args.config, "r") as config_file:
        config = json.load(config_file)

    group_id = config.get("group_id", None)
    payer_name = config.get("payer_name", None)

    # Raise an exception if group_id or payer_name is not found
    if group_id is None:
        raise ValueError("No group_id found in the configuration file!")
    if payer_name is None:
        raise ValueError("No payer_name found in the configuration file!")

    # Fetch the group members and create a name-to-ID mapping
    name_to_id = splitwise_client.get_group_members(group_id)
    if "Unknown None" in name_to_id:
        name_to_id[UNKNOWN_MEMBER_KEY] = name_to_id.pop("Unknown None")
    actual_members = [x for x in list(
        name_to_id.keys()) if x != UNKNOWN_MEMBER_KEY]

    # Upload file and create assistant
    statement_parser = Bayclub_statement_parser(members=actual_members)
    parsed_statement = statement_parser.upload_and_parse(args.statement_pdf)

    logging.info("Got parsed statement. Thank you GPT <3")
    print(parsed_statement)

    # Process the CSV and add expenses
    expenses = process_statement(
        parsed_statement, group_id, payer_name, name_to_id)

    pprint.pprint(expenses)

    if args.upload_to_splitwise:
        logging.info("Uploading expenses to splitwise...")
        for expense in expenses:
            splitwise_client.add_expense(expense)
    else:
        logging.info("NOT uploading to splitwise.")

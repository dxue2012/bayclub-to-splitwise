import asyncio
import json
import sys
from datetime import datetime

import pandas as pd
from openai import OpenAI
from requests_oauthlib import OAuth1Session


class Splitwise_client:
    def __init__(self, secrets):
        consumer_key = secrets["consumer_key"]
        consumer_secret = secrets["consumer_secret"]
        access_token = secrets["access_token"]
        access_token_secret = secrets["access_token_secret"]

        self.oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

    def get_group_members(self, group_id):
        """Fetch the members of a group and return a dictionary mapping full names to user IDs."""

        # Set the endpoint URL to get group details
        url = f"https://secure.splitwise.com/api/v3.0/get_group/{group_id}"
        # Send the request to Splitwise to get group details
        response = self.oauth.get(url)

        if response.status_code == 200:
            group_info = response.json()
            members = group_info["group"]["members"]

            # Create a dictionary mapping full name to user ID
            name_to_id = {}
            for member in members:
                first_name = member["first_name"]
                last_name = member.get("last_name", "")
                full_name = f"{first_name} {last_name}".strip()
                name_to_id[full_name] = member["id"]

            return name_to_id
        else:
            print(f"Failed to get group details: {response.status_code}")
            print(response.text)
            return {}

    def add_expense(self, expense):
        """Create a new expense on Splitwise using user IDs."""

        (cost, description, date, group_id, user_shares) = expense

        # Set the endpoint URL to create an expense
        url = "https://secure.splitwise.com/api/v3.0/create_expense"

        # Prepare the expense data, including date
        data = {
            "cost": str(cost),
            "description": description,
            "date": date,  # Add the date here in the format YYYY-MM-DD
            "group_id": group_id,  # Must be provided
        }

        # Add users and their shares in the indexed format (users__0__user_id, etc.)
        for index, (user_id, shares) in enumerate(user_shares.items()):
            data[f"users__{index}__user_id"] = user_id  # Use user_id instead of names
            data[f"users__{index}__paid_share"] = f"{shares['paid']:.2f}"
            data[f"users__{index}__owed_share"] = f"{shares['owed']:.2f}"

        # Send the request to Splitwise to create the expense
        response = self.oauth.post(url, data=data)

        if response.status_code == 200:
            response = response.json()
            errors = response["errors"]
            if not errors:
                print("Expense created successfully!")
            else:
                print("Got an error", "Tried to submit data", data)
                print("The error was", errors)
        else:
            print(f"Failed to create expense: {response.status_code}")
            print(response.text)


def process_csv(csv_file, group_id, payer_name, name_to_id):
    """Process the CSV and add expenses using Splitwise user IDs."""
    # Load the CSV
    df = pd.read_csv(csv_file)

    # Get the payer's user ID from the group member mapping
    payer_user_id = name_to_id.get(payer_name)

    if not payer_user_id:
        raise Exception(f"Error: Payer '{payer_name}' not found in the group!")

    # Loop through each row and process the data
    for _, row in df.iterrows():
        date_raw = row[0]  # Assuming the date is in the first column
        cost = row[1]  # Assuming cost is in the second column
        description = row[2]  # Assuming description is in the third column
        member = row[3]  # Assuming member is in the fourth column

        # Skip rows where the cost is negative
        if cost < 0:
            continue

        # Parse the date into the required YYYY-MM-DD format
        try:
            date = datetime.strptime(date_raw, "%m/%d/%y").strftime("%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format for row: {row}")
            continue

        user_shares = {}

        # Handle cases where the member is "Unknown"
        if member == "All":
            # Split equally among all members (except "Unknown")
            actual_members = {k: v for k, v in name_to_id.items() if k != "Unknown"}
            num_members = len(actual_members)

            # Calculate each member's share
            owed_amount_per_member = cost / num_members

            # Assign shares (Payer pays, everyone owes equally)
            for member_name, member_id in actual_members.items():
                paid = cost if member_name == payer_name else 0
                user_shares[member_id] = {"paid": paid, "owed": owed_amount_per_member}

        else:
            # Regular case with known members
            # Use the payer's user ID and the other member's ID (retrieved from name_to_id)
            other_member_id = name_to_id.get(member)
            if not other_member_id:
                print(f"Error: Could not find member '{member}' in the group.")
                continue

            user_shares = {
                payer_user_id: {"paid": cost, "owed": 0},  # Payer pays the full amount
                other_member_id: {
                    "paid": 0,
                    "owed": cost,
                },  # Other member owes the full cost
            }

        yield (cost, description, date, group_id, user_shares)


class OpenAI_pdf_parser:
    def __init__(self):
        self.client = OpenAI().beta

        instructions = """You are a helpful assistant who is proficient at parsing PDFs and processing data.

        You will be given PDFs that represent billing statements for a group, and you are tasked with
        processing it into a table (in CSV format).

        1. Use quotes to escape commas
        2. Derive a "Responsible person" column that is either one of the members, or “All” or “Unknown”. The members are "Dyland Xue, Yi Zhong, Amber Shen, Qinyu Wang, Suyi Liu, and Eddie Chen". 
            1. If it's unclear who owns the row, just write "Unknown”.
            2. Dues are always “All” regardless of what name is associated with the row in the PDF.
            3. Only parse the user name if it's not surrounded by parens. e.g. "No Show Fee (Y Zhong) No Show Fee Amber Shen" should be assigned to Amber Shen, not Yi Zhong
            4. If multiple names show up, use the first one, e.g. "Court Fee 8/10 amber shen court time Yi Zhong primary" should be assigned to "Amber Shen" instead of "Yi Zhong"
        3. Use the columns “Date,Amount,Description,Responsible Person” in the CSV output
        4. Print out the CSV in the conversation, but also offer it as a file to download
        """

        self.assistant = self.client.assistants.create(
            name="PDF Parser",
            instructions=instructions,
            model="GPT-4o",
            tools=[{"type": "file_search"}],
        )

    def upload_and_parse(self, file_path):
        vector_store = self.client.vector_stores.create(name="Statement PDFs")
        file_id = self.client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id, file=file_path, poll_interval_ms=100
        )

        vector_store = self.create_vector_store()
        self.add_file_to_vector_store(vector_store, file_id)
        thread = self.client.threads.create(assistant_id=self.assistant.id)
        _ = self.client.threads.messages.create(
            thread_id=thread.id, role="user", content="Can you please parse this PDF?"
        )

        run = self.client.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=self.assistant.id
        )

        while run.status != "completed":
            print("Polling run status...", run.status)
            asyncio.sleep(1)

        messages = self.client.threads.messages.list(thread_id=thread.id)

        return messages


if __name__ == "__main__":
    # Command line arguments: csv_path and config_path
    if len(sys.argv) != 3:
        print("Usage: python your_script.py <pdf_path> <config_path>")
        sys.exit(1)

    with open("secrets.json", "r") as file:
        secrets = json.load(file)
        print("loaded splitwise secrets")

    # Upload file and create assistant
    pdf_parser = OpenAI_pdf_parser()
    pdf_path = sys.argv[1]
    response = pdf_parser.upload_and_parse(pdf_path)
    print(response)

    print("queried GPT")

    config_file_path = sys.argv[2]
    # Load the config JSON to get the group_id and payer name
    with open(config_file_path, "r") as config_file:
        config = json.load(config_file)
        print("loaded splitwise config")

    group_id = config.get("group_id", None)
    payer_name = config.get("payer_name", None)

    # Raise an exception if group_id or payer_name is not found
    if group_id is None:
        raise Exception("No group_id found in the configuration file!")
    if payer_name is None:
        raise Exception("No payer_name found in the configuration file!")

    splitwise_client = Splitwise_client(secrets)

    # Fetch the group members and create a name-to-ID mapping
    name_to_id = splitwise_client.get_group_members(group_id)

    # Process the CSV and add expenses
    # for expense in process_csv(csv_file_path, group_id, payer_name, name_to_id):
    #     print(expense)
    # splitwise_client.add_expense(expense)

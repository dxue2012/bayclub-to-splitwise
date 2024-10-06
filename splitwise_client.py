import json

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

    def get_all_expenses(self, group_id):
        """Fetch all expenses in a group."""

        # Set the endpoint URL to get group details
        url = f"https://secure.splitwise.com/api/v3.0/get_expenses?group_id={group_id}"
        # Send the request to Splitwise to get group details

        response = self.oauth.get(url)

        if response.status_code == 200:
            expenses = response.json()
            print(json.dumps(expenses, indent=4))
            return expenses
        else:
            print(f"Failed to get group expenses: {response.status_code}")
            print(response.text)
            return {}

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

        (cost, description, date, group_id, user_shares, details) = expense

        # Set the endpoint URL to create an expense
        url = "https://secure.splitwise.com/api/v3.0/create_expense"

        # Prepare the expense data, including date
        data = {
            "cost": str(cost),
            "description": description,
            "details": details,
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

    def delete_expense(self, expense_id):
        """Delete an expense."""

        # Set the endpoint URL to create an expense
        url = f"https://secure.splitwise.com/api/v3.0/delete_expense/{expense_id}"

        # Send the request to Splitwise to create the expense
        response = self.oauth.post(url, data={})

        if response.status_code == 200:
            response = response.json()
            errors = response["errors"]
            if not errors:
                print("Expense deleted successfully!")
            else:
                print("Got an error")
                print("The error was", errors)
        else:
            print(f"Failed to delete expense: {response.status_code}")
            print(response.text)

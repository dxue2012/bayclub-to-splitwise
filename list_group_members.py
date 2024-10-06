import json
from requests_oauthlib import OAuth1Session

# Load secrets from secrets.json


def load_secrets(file_path="secrets.json"):
    with open(file_path, "r") as file:
        return json.load(file)


def list_group_members(group_id):
    # Load credentials and access tokens from secrets.json
    secrets = load_secrets()

    consumer_key = secrets["consumer_key"]
    consumer_secret = secrets["consumer_secret"]
    access_token = secrets["access_token"]
    access_token_secret = secrets["access_token_secret"]

    # Set the endpoint URL to get group details
    url = f"https://secure.splitwise.com/api/v3.0/get_group/{group_id}"
    oauth = OAuth1Session(consumer_key,
                          client_secret=consumer_secret,
                          resource_owner_key=access_token,
                          resource_owner_secret=access_token_secret)

    # Send the request to Splitwise to get group details
    response = oauth.get(url)

    if response.status_code == 200:
        group_info = response.json()
        members = group_info['group']['members']

        # Print all members and their user IDs
        print(f"Members of Group {group_id}:")
        for member in members:
            user_id = member['id']
            first_name = member['first_name']
            last_name = member['last_name']
            print(f"User ID: {user_id}, Name: {first_name} {last_name}")
    else:
        print(f"Failed to get group details: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    group_id = input("Enter the group ID: ")
    list_group_members(group_id)

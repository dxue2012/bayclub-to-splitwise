import json
from requests_oauthlib import OAuth1Session

# Load secrets from secrets.json


def load_secrets(file_path="secrets.json"):
    with open(file_path, "r") as file:
        return json.load(file)


def print_current_user():
    # Load credentials and access tokens from secrets.json
    secrets = load_secrets()

    consumer_key = secrets["consumer_key"]
    consumer_secret = secrets["consumer_secret"]
    access_token = secrets["access_token"]
    access_token_secret = secrets["access_token_secret"]

    # Make the authenticated request to get the current user
    url = "https://secure.splitwise.com/api/v3.0/get_current_user"
    oauth = OAuth1Session(consumer_key,
                          client_secret=consumer_secret,
                          resource_owner_key=access_token,
                          resource_owner_secret=access_token_secret)

    response = oauth.get(url)

    if response.status_code == 200:
        user_info = response.json()
        user = user_info["user"]
        print(f"User ID: {user['id']}")
        print(f"Name: {user['first_name']} {user.get('last_name', '')}")
        print(f"Email: {user['email']}")
    else:
        print(f"Failed to get current user: {response.status_code}")


def print_friends():
    # Load credentials and access tokens from secrets.json
    secrets = load_secrets()

    consumer_key = secrets["consumer_key"]
    consumer_secret = secrets["consumer_secret"]
    access_token = secrets["access_token"]
    access_token_secret = secrets["access_token_secret"]

    # Make the authenticated request to get friends
    url = "https://secure.splitwise.com/api/v3.0/get_friends"
    oauth = OAuth1Session(consumer_key,
                          client_secret=consumer_secret,
                          resource_owner_key=access_token,
                          resource_owner_secret=access_token_secret)

    response = oauth.get(url)

    if response.status_code == 200:
        friends = response.json()
        print("Your friends:")
        for friend in friends['friends']:
            friend_name = f"{friend['first_name']} {friend.get('last_name', '')}"
            friend_id = friend['id']
            print(f"User ID: {friend_id}, Name: {friend_name}")
    else:
        print(f"Failed to get friends: {response.status_code}")


if __name__ == "__main__":
    print_current_user()

    # Just print friends using the stored access tokens
    print_friends()

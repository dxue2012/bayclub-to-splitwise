import json
import webbrowser
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

# Load secrets from secrets.json


def load_secrets(file_path="secrets.json"):
    with open(file_path, "r") as file:
        return json.load(file)


def authenticate_with_splitwise():
    # Load credentials
    secrets = load_secrets()

    client_id = secrets["consumer_key"]
    client_secret = secrets["consumer_secret"]
    authorization_base_url = "https://secure.splitwise.com/oauth/authorize"
    token_url = "https://secure.splitwise.com/oauth/token"
    # or use http://localhost:8000 for local testing
    redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

    # Step 1: Create OAuth2 session
    splitwise = OAuth2Session(client_id, redirect_uri=redirect_uri)

    # Step 2: Redirect user to Splitwise for authorization
    authorization_url, state = splitwise.authorization_url(
        authorization_base_url)
    print(f"Go to this URL to authorize: {authorization_url}")

    # Open the browser to authorize the app
    webbrowser.open(authorization_url)

    # Step 3: Get the authorization verifier code from the callback URL
    authorization_response = input("Paste the full callback URL here: ")

    # Step 4: Fetch the access token using the authorization code
    token = splitwise.fetch_token(token_url, authorization_response=authorization_response,
                                  client_secret=client_secret)

    # Step 5: Save access token to secrets.json
    secrets["access_token"] = token['access_token']
    with open("secrets.json", "w") as file:
        json.dump(secrets, file, indent=4)

    print("Access token saved in secrets.json!")


if __name__ == "__main__":
    authenticate_with_splitwise()

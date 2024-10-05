from splitwise import Splitwise
from splitwise.expense import Expense, ExpenseUser

# Set up your keys
CONSUMER_KEY = 'your_consumer_key'
CONSUMER_SECRET = 'your_consumer_secret'
ACCESS_TOKEN = 'your_access_token'
ACCESS_TOKEN_SECRET = 'your_access_token_secret'

# Authenticate with Splitwise
sObj = Splitwise(CONSUMER_KEY, CONSUMER_SECRET)
sObj.setOAuth1AccessToken(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Create a function to add a charge


def add_expense(cost, description, group_id, user_shares):
    # Create a new expense object
    expense = Expense()
    expense.setCost(cost)
    expense.setDescription(description)
    expense.setGroupId(group_id)

    users = []
    for user_id, share in user_shares.items():
        user = ExpenseUser()
        user.setId(user_id)
        user.setPaidShare(0)  # This user hasn't paid yet
        user.setOwedShare(share)  # This is what they owe
        users.append(user)

    expense.setUsers(users)

    # Create the expense on Splitwise
    created_expense = sObj.createExpense(expense)

    if created_expense:
        print("Expense created successfully!")
    else:
        print("Failed to create expense.")


# Example usage
# You need to replace with actual user ids from Splitwise and a valid group id.
cost = "100.00"
description = "Dinner"
group_id = 123456  # Replace with your group ID
user_shares = {
    12345: "50.00",  # Replace with actual user ID and their share
    67890: "50.00"   # Replace with actual user ID and their share
}

add_expense(cost, description, group_id, user_shares)

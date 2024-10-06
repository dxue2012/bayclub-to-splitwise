A few python scripts that automatically convert billing statements from [Bay
Club](https://www.bayclubs.com/) into [SplitWise](https://www.splitwise.com/) Expenses.

## Problem Statement

You're in a friend group with a group membership at Bay Club. One of you are the account
holder who receives the monthly statement and pays the bills. At the end of each month,
you use SplitWise to charge and settle with your friends.

However, there are lots of individual line items on each statement (e.g. Court Fee, 
Tennis Lesson, etc.) that should be assigned to an individual. This creates some
annoyance:

1. It's a lot of tedious typing to transcribe to statement into SplitWise items
2. It's something difficult to figure out who's responsible for a charge due to Bay Club
sometimes putting multiple members (or none) on the line

## How this repo helps

The script here

1. Uses openai's API to ask GPT to convert the statement PDF into a JSON.
2. The script then converts each line into a SplitWise expense and uploads it to a
SplitWise group, using the SplitWise API, for potentially more manual processing.

There are some auxiliary scripts that help with the process, e.g. for getting the initial
OAuth tokens from SplitWise, getting user IDs from SplitWise, or deleting test expenses
etc. 

A few interesting choices:

- As part of the PDF->JSON converion, GPT also assigns each line to one of the members in
  the SplitWise group using a set of heuristics I've discovered to kinda work (tested on 2
  months of historical data).
- Charges that cannot be easily associated with any member are assigned to "Unknown",
  which must be a member in the SplitWise group.

This allows members to manually resolve incorrect assignments in SplitWise with the
maximum amount of information.


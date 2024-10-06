A few python scripts that automatically convert billing statements from [Bay
Club](https://www.bayclubs.com/) into [SplitWise](https://www.splitwise.com/) Expenses.

## What are we trying to solve?

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

1. First uses openai's API to ask GPT to convert the statement PDF into a JSON.
2. Then converts each line into a SplitWise expense and uploads it to a
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

## How to use

### Dependencies

1. Install deps using conda - the environment is captured into `environment.yml`. 
2. Run `python3 auth.py` to initialize the SplitWise API - store the values in a
   `secrets.json`.
3. Make sure you can use oai's APIs - log in to your openai account and follow the steps
   there (and add a few $ to your account) if you've never used it before.

### Actually running it

```
python3 upload_to_splitwise.py --statement=PATH_TO_YOUR_STATEMENT_PDF --config=config.json
```

`config.json` must contain a `payer_name` (the person who pays the Bay Club bills), and a
SplitWise `group_id`.

By default `upload_to_splitwise.py` does a dry-run; add the flag `--upload-to-splitwise`
to actually upload to SplitWise.

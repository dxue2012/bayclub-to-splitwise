import argparse
import json

from splitwise_client import Splitwise_client


def parse_args():
    parser = argparse.ArgumentParser(
        description="Parse a bayclub statement and upload charges to splitwise"
    )

    # Two positional arguments for file paths
    parser.add_argument("--config", type=str, help="The path to the config JSON.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    with open(args.config, "r") as config_file:
        config = json.load(config_file)

    with open("secrets.json", "r") as file:
        secrets = json.load(file)

    group_id = config.get("group_id", None)

    splitwise_client = Splitwise_client(secrets)
    splitwise_client.get_all_expenses(group_id)

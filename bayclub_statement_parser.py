import io
from typing import List

import openai
import pandas as pd
from pydantic import BaseModel


class Row(BaseModel):
    date: str
    amount: str
    description: str
    assigned_member: str
    reason: str


class Parsed_statement(BaseModel):
    rows: list[Row]


# Maybe one day I'll use this:
#             response_format={
#               "type": "json_schema",
#               "json_schema": {
#                   "name": "Prased_statement",
#                   "schema": Parsed_statement.model_json_schema(),
#               },
#           },


class MissingOutputError(Exception):
    pass


class AmbiguousOutputError(Exception):
    def __init__(self, outputs):
        output = '\n'.join(outputs)
        self.message = f"Got outputs {output}"
        super().__init__(self.message)


class Bayclub_statement_parser:
    def __init__(self, members: List[str]):
        self.client = openai.OpenAI()

        instructions = f"""You are a helpful assistant who is proficient at parsing PDFs and processing data.

        You will be given PDFs that represent billing statements for a group, and you are tasked with
        processing it into a table (in JSON format).

        1. Use quotes to escape commas
        2. Derive a "Responsible person" column that is either one of the members, or “All” or “Unknown”. The members are "{members}". 
        3. Use the following keys for each row in the JSON output: “Date,Amount,Description,Assigned_member,Reason”, where reason is your rationale for how you derived the responsible person (see more about rules below).
        4. Include the full description (e.g. merge multiple lines into one if necessary) for human consumption
        5. Offer the result as a file to download, no need to print out the JSON as part of the conversation

        Here are the rules for deriving the responsible person from the row description:
        
        1. Dues are always “All” regardless of what name is associated with the row in the PDF.
        2. Only parse the user name if it's not surrounded by parens. e.g. "No Show Fee (Amy Buffet) No Show Fee John Doe" should be assigned to John Doe, not Amy Buffet
        3. ASSIGN TO THE FIRST NAME IF MULTIPLE NAMES SHOW UP regardless of case, e.g. "Court Fee 8/10 {members[0]} court time {members[1]} primary" should be assigned to "{members[0]}" instead of "{members[1]}"
        4. If it sounds like a shared responsibility, e.g. "shared membership ..." assign it to "All"
        5. Assign to "Unknown" if you can't figure it out.
        6.  The first 3 are hard rules. 4 and 5 are soft and require some judgment.

        Remember to think step by step, and double check your work.
        """

        self.assistant = self.client.beta.assistants.create(
            name="PDF Parser",
            instructions=instructions,
            model="gpt-4o",
            tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
            temperature=0.5,
        )

    def upload_and_parse(self, file_path):
        message_file = self.client.files.create(
            file=open(file_path, "rb"), purpose="assistants"
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": "Please parse this PDF and offer a link to download the JSON.",
                    "attachments": [
                        {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
                    ],
                }
            ]
        )

        print("querying GPT. This may take a while...")

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=self.assistant.id, poll_interval_ms=1000
        )

        messages = list(
            self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
        )

        message_content = messages[0].content[0].text
        annotations = message_content.annotations
        output_files = []

        for annotation in annotations:
            if file_path := getattr(annotation, "file_citation", None):
                output_files.append(file_path)
            if file_path := getattr(annotation, "file_path", None):
                output_files.append(file_path)

        if len(output_files) == 0:
            print(message_content)
            raise MissingOutputError

        if len(output_files) > 1:
            print(message_content)
            raise AmbiguousOutputError(output_files)

        file_contents = self.client.files.content(output_files[0].file_id)
        return pd.read_json(io.BytesIO(file_contents.content))

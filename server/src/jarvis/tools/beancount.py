import logging
from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from datetime import datetime
import os
from github import Github
from github.ContentFile import ContentFile
from github.InputGitTreeElement import InputGitTreeElement
from github.Auth import Token


_LOGGER = logging.getLogger(__name__)


class BeancountAddTransactionInput(BaseModel):
    date: datetime = Field(description="Transaction date")
    payee: Optional[str] = Field(description="Transaction payee")
    comment: str = Field(description="Transaction comment")
    account_from: str = Field(description="Account where money were debited from")
    account_to: str = Field(description="Account where money were credited to")
    amount: float = Field(description="Transaction value")


class BeancountAddTransactionTool(BaseTool):
    name = "beacount_add_transaction"
    description = "Add a transaction to personal beancount accounting ledger."
    args_schema: Type[BaseModel] = BeancountAddTransactionInput

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(
        self,
        date: datetime,
        payee: Optional[str],
        comment: str,
        account_from: str,
        account_to: str,
        amount: float,
    ) -> str:
        try:
            github = Github(auth=Token(os.environ["GITHUB_API_KEY_JARVIS"]))

            repo = github.get_repo("comigor/beancount")
            file_path = "beancount/2024.beancount"

            # Get a reference to the desired branch
            head_ref = repo.get_git_ref("heads/master")

            # Get the commit object on the branch tip (HEAD)
            commit = repo.get_git_commit(head_ref.object.sha)

            # Get the file content from the commit using the Get Contents API
            file_content = repo.get_contents(path=file_path, ref=commit.sha)
            if isinstance(file_content, ContentFile):
                file_content = file_content.decoded_content.decode()

            # Create a new blob object with the edited content
            blob = repo.create_git_blob(
                f"""{file_content}
{date.strftime("%Y-%m-%d")} * "{payee}" "{comment}"
  {account_to} {"{:.2f}".format(amount)} BRL
  {account_from}
""",
                "utf-8",
            )

            # Create a new tree object with the updated file
            tree = repo.create_git_tree(
                [
                    InputGitTreeElement(
                        file_path, type="blob", mode="100644", sha=blob.sha
                    )
                ],
                base_tree=commit.tree,
            )

            # Create a new commit object with the updated tree and parent commit
            new_commit = repo.create_git_commit(
                "From JARVIS", tree=tree, parents=[commit]
            )

            head_ref.edit(sha=new_commit.sha, force=False)
        except Exception as e:
            _LOGGER.error(f"Error: {e}")
            return f"Sorry, I can't do that."

        return "Transaction added."

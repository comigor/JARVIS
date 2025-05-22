import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os

# Ensure imports from jarvis.tools are possible
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from jarvis.tools.beancount import BeancountAddTransactionTool, BeancountAddTransactionInput

class TestBeancountAddTransactionTool(unittest.TestCase):

    @patch.dict(os.environ, {"GITHUB_API_KEY_JARVIS": "test_token"})
    @patch('jarvis.tools.beancount.Github')
    def test_run_success(self, MockGithub):
        # Setup mock Github client and repo
        mock_github_instance = MockGithub.return_value
        mock_repo = mock_github_instance.get_repo.return_value
        mock_head_ref = MagicMock()
        mock_head_ref.object.sha = "test_sha"
        mock_repo.get_git_ref.return_value = mock_head_ref
        
        mock_commit = MagicMock()
        mock_repo.get_git_commit.return_value = mock_commit
        mock_commit.tree = "test_tree_sha" # Keep it simple, or create a MagicMock for tree if needed

        mock_file_content = MagicMock()
        mock_file_content.decoded_content = b"existing content\n"
        mock_repo.get_contents.return_value = mock_file_content

        mock_blob = MagicMock()
        mock_blob.sha = "new_blob_sha"
        mock_repo.create_git_blob.return_value = mock_blob

        tool = BeancountAddTransactionTool()
        
        # Test data
        test_date = datetime(2024, 1, 15)
        payee = "Test Payee"
        comment = "Test transaction"
        account_from = "Assets:Checking"
        account_to = "Expenses:Groceries"
        amount = 50.0

        result = tool._run(
            date=test_date,
            payee=payee,
            comment=comment,
            account_from=account_from,
            account_to=account_to,
            amount=amount
        )

        self.assertEqual(result, "Transaction added.")
        
        # Check that Github was called
        MockGithub.assert_called_once()
        mock_repo.get_repo.assert_called_with("comigor/beancount")
        mock_repo.get_contents.assert_called_with(path="beancount/2024.beancount", ref="test_sha")
        
        expected_blob_content = f"""existing content

2024-01-15 * "{payee}" "{comment}"
  {account_to} {amount:.2f} BRL
  {account_from}
"""
        mock_repo.create_git_blob.assert_called_with(expected_blob_content, "utf-8")
        mock_repo.create_git_tree.assert_called_once()
        mock_repo.create_git_commit.assert_called_once()
        mock_head_ref.edit.assert_called_once()

    @patch.dict(os.environ, {"GITHUB_API_KEY_JARVIS": "test_token"})
    @patch('jarvis.tools.beancount.Github')
    def test_run_github_exception(self, MockGithub):
        # Setup mock Github client to raise an exception
        mock_github_instance = MockGithub.return_value
        mock_github_instance.get_repo.side_effect = Exception("GitHub API error")

        tool = BeancountAddTransactionTool()
        
        result = tool._run(
            date=datetime.now(),
            payee="Test",
            comment="Test",
            account_from="Assets:Test",
            account_to="Expenses:Test",
            amount=10.0
        )
        self.assertEqual(result, "Sorry, I can't do that.")

if __name__ == '__main__':
    unittest.main()

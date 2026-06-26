import unittest
import sys
import os

# Adjust paths to import lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.validation import validate_and_normalize_email, validate_and_format_phone

class TestValidation(unittest.TestCase):
    def test_valid_emails(self):
        self.assertEqual(validate_and_normalize_email("user@example.com"), "user@example.com")
        self.assertEqual(validate_and_normalize_email("USER.name+tag@Gmail.com"), "USER.name+tag@gmail.com")

    def test_disposable_emails(self):
        disposables = ["test@mailinator.com", "user@yopmail.com", "random@10minutemail.com"]
        for email in disposables:
            with self.assertRaises(ValueError):
                validate_and_normalize_email(email)

    def test_bot_emails(self):
        bots = ["test@test.com", "admin@admin.com", "root@root.com"]
        for email in bots:
            with self.assertRaises(ValueError):
                validate_and_normalize_email(email)

    def test_fake_keywords(self):
        fake_emails = ["mytestemail@gmail.com", "fake_user@domain.com", "dummyperson@example.org"]
        for email in fake_emails:
            with self.assertRaises(ValueError):
                validate_and_normalize_email(email)

    def test_invalid_email_format(self):
        invalids = ["invalid-email", "user@", "@domain.com", "user@domain"]
        for email in invalids:
            with self.assertRaises(ValueError):
                validate_and_normalize_email(email)

    def test_valid_phones(self):
        # phonenumbers expects country code or will raise if country is None and no + prefix
        self.assertEqual(validate_and_format_phone("+1 415 555 2671"), "+14155552671")
        self.assertEqual(validate_and_format_phone("+91 98765 43210"), "+919876543210")

    def test_invalid_phones(self):
        invalids = ["12345", "+1 123", "not-a-number", ""]
        for phone in invalids:
            with self.assertRaises(ValueError):
                validate_and_format_phone(phone)

if __name__ == "__main__":
    unittest.main()

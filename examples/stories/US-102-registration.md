# US-102: Register an account

As a new customer
I want to create an account
So that I can track my orders

## Acceptance criteria

- AC1: Given I am on the registration page, when I submit a valid email address and password, then my account is created and I am logged in
- AC2: The password must be at least 8 characters and no more than 64 characters
- AC3: An email address that is already registered is rejected with the message "An account with this email already exists"
- AC4: The display name is required and must be no more than 30 characters
- AC5: The password is never shown in plain text on the page or in confirmation emails

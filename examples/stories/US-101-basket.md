# US-101: Add a book to the basket

As a customer
I want to add books to my basket
So that I can buy several books in one order

## Acceptance criteria

- AC1: Given I am viewing a book that is in stock, when I click "Add to basket", then the basket count increases by 1
- AC2: The quantity of a single book in the basket must be between 1 and 10
- AC3: A book that is out of stock cannot be added and the page shows an "Out of stock" message
- AC4: Given I am not logged in, when I add a book, then the basket is kept for my session and I am asked to log in at checkout

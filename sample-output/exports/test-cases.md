# Generated test cases

## US-101

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-001 | positive | high | Verify the basket count increases by 1 | 1. I click "Add to basket" | The basket count increases by 1 | US-101/AC1 |
| TC-002 | positive | high | A valid quantity within the allowed range is accepted | 1. Go to the 'Add a book to the basket' journey<br>2. Enter a typical valid quantity<br>3. Submit | The value is accepted and the journey continues | US-101/AC2 |
| TC-003 | boundary | medium | Quantity of 0 is rejected (below minimum 1) | 1. Go to the 'Add a book to the basket' journey<br>2. Enter a quantity of 0<br>3. Submit | A validation message explains the limit | US-101/AC2 |
| TC-004 | boundary | medium | Quantity of 1 is accepted (minimum) | 1. Go to the 'Add a book to the basket' journey<br>2. Enter a quantity of 1<br>3. Submit | The value is accepted | US-101/AC2 |
| TC-005 | boundary | medium | Quantity of 10 is accepted (maximum) | 1. Go to the 'Add a book to the basket' journey<br>2. Enter a quantity of 10<br>3. Submit | The value is accepted | US-101/AC2 |
| TC-006 | boundary | medium | Quantity of 11 is rejected (above maximum 10) | 1. Go to the 'Add a book to the basket' journey<br>2. Enter a quantity of 11<br>3. Submit | A validation message explains the limit | US-101/AC2 |
| TC-007 | negative | medium | Rule is enforced: A book that is out of stock cannot be added and the page shows an "... | 1. Go to the 'Add a book to the basket' journey<br>2. Attempt the action the rule forbids | The message "Out of stock" is shown | US-101/AC3 |
| TC-008 | positive | high | Verify the basket is kept for my session and I am asked to log in at checkout | 1. I add a book | The basket is kept for my session and I am asked to log in at checkout | US-101/AC4 |
| TC-009 | security | high | Protected steps of 'Add a book to the basket' require login | 1. Make sure no user is logged in<br>2. Go directly to the 'Add a book to the basket' pages | The user is asked to log in and no protected data is shown | US-101/AC4 |

## US-102

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-010 | positive | high | Verify my account is created and I am logged in | 1. I submit a valid email address and password | My account is created and I am logged in | US-102/AC1 |
| TC-011 | security | medium | Injection payloads in the email address field are rejected or safely escaped | 1. Enter <script>alert(1)</script> and ' OR '1'='1 in the email address field<br>2. Submit | Input is rejected or rendered as plain text; no script runs, no server error | US-102/AC1, US-102/AC3 |
| TC-012 | security | medium | Injection payloads in the password field are rejected or safely escaped | 1. Enter <script>alert(1)</script> and ' OR '1'='1 in the password field<br>2. Submit | Input is rejected or rendered as plain text; no script runs, no server error | US-102/AC1, US-102/AC2, US-102/AC5 |
| TC-013 | positive | high | A valid password within the allowed range is accepted | 1. Go to the 'Register an account' journey<br>2. Enter a typical valid password<br>3. Submit | The value is accepted and the journey continues | US-102/AC2 |
| TC-014 | boundary | medium | Password with 7 characters is rejected (below minimum 8) | 1. Go to the 'Register an account' journey<br>2. Enter a password with 7 characters<br>3. Submit | A validation message explains the limit | US-102/AC2 |
| TC-015 | boundary | medium | Password with 8 characters is accepted (minimum) | 1. Go to the 'Register an account' journey<br>2. Enter a password with 8 characters<br>3. Submit | The value is accepted | US-102/AC2 |
| TC-016 | boundary | medium | Password with 64 characters is accepted (maximum) | 1. Go to the 'Register an account' journey<br>2. Enter a password with 64 characters<br>3. Submit | The value is accepted | US-102/AC2 |
| TC-017 | boundary | medium | Password with 65 characters is rejected (above maximum 64) | 1. Go to the 'Register an account' journey<br>2. Enter a password with 65 characters<br>3. Submit | A validation message explains the limit | US-102/AC2 |
| TC-018 | negative | medium | Rule is enforced: An email address that is already registered is rejected with the me... | 1. Go to the 'Register an account' journey<br>2. Attempt the action the rule forbids | The message "An account with this email already exists" is shown | US-102/AC3 |
| TC-019 | positive | high | A valid display name within the allowed range is accepted | 1. Go to the 'Register an account' journey<br>2. Enter a typical valid display name<br>3. Submit | The value is accepted and the journey continues | US-102/AC4 |
| TC-020 | boundary | medium | Display name with 30 characters is accepted (maximum) | 1. Go to the 'Register an account' journey<br>2. Enter a display name with 30 characters<br>3. Submit | The value is accepted | US-102/AC4 |
| TC-021 | boundary | medium | Display name with 31 characters is rejected (above maximum 30) | 1. Go to the 'Register an account' journey<br>2. Enter a display name with 31 characters<br>3. Submit | A validation message explains the limit | US-102/AC4 |
| TC-022 | negative | medium | Submitting without display name is rejected | 1. Go to the 'Register an account' journey<br>2. Leave display name empty<br>3. Submit | A validation message says display name is required | US-102/AC4 |
| TC-023 | security | medium | Injection payloads in the display name field are rejected or safely escaped | 1. Enter <script>alert(1)</script> and ' OR '1'='1 in the display name field<br>2. Submit | Input is rejected or rendered as plain text; no script runs, no server error | US-102/AC4 |
| TC-024 | security | high | Password is masked on screen and never echoed back | 1. Type a password into the form<br>2. Submit<br>3. Check the page and any emails sent | The password is masked while typing and never appears in plain text | US-102/AC5 |

## US-103

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-025 | positive | high | Verify I see 3 orders listed with the newest first | 1. I open "My orders" | I see 3 orders listed with the newest first | US-103/AC1 |
| TC-026 | security | high | Protected steps of 'View order history' require login | 1. Make sure no user is logged in<br>2. Go directly to the 'View order history' pages | The user is asked to log in and no protected data is shown | US-103/AC1, US-103/AC2 |
| TC-027 | positive | high | Verify I see at most 20 orders per page and a link to the next page | 1. I open "My orders" | I see at most 20 orders per page and a link to the next page | US-103/AC2 |
| TC-028 | boundary | medium | Behaviour at 20 orders (maximum) | 1. Set up data so the scenario involves 20 orders<br>2. I open "My orders" | The rule holds exactly at the limit | US-103/AC2 |
| TC-029 | boundary | medium | Behaviour at 21 orders (above maximum 20) | 1. Set up data so the scenario involves 21 orders<br>2. I open "My orders" | The limit is enforced: I see at most 20 orders per page and a link to the next page | US-103/AC2 |
| TC-030 | positive | high | Verify I see an "Access denied" message and no order details | 1. I open the order page URL of a different customer | I see an "Access denied" message and no order details | US-103/AC3 |
| TC-031 | negative | medium | Rule is enforced: Another customer's order is not visible | 1. Go to the 'View order history' journey<br>2. Attempt the action the rule forbids | The message "Access denied" is shown | US-103/AC3 |
| TC-032 | security | high | Changing the record id in the URL does not expose another customer's data | 1. Log in as customer A<br>2. Open a URL containing customer B's record id | Access is denied and no data belonging to customer B is shown | US-103/AC3 |

## GET /health

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-033 | positive | high | Health check succeeds with valid input | 1. Send GET /health with valid parameters and body | Response status is 200 | GET /health, GET /health 200 |

## GET /books

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-034 | positive | high | List books succeeds with valid input | 1. Send GET /books with valid parameters and body | Response status is 200 | GET /books, GET /books 200 |
| TC-035 | boundary | medium | List books: query limit at minimum (1) is accepted | 1. Send GET /books with limit=1 | Response status is 200 | GET /books, GET /books 200 |
| TC-036 | boundary | medium | List books: query limit below minimum (1) is rejected | 1. Send GET /books with limit=0 | Response status is 400 | GET /books, GET /books 400 |
| TC-037 | boundary | medium | List books: query limit at maximum (100) is accepted | 1. Send GET /books with limit=100 | Response status is 200 | GET /books, GET /books 200 |
| TC-038 | boundary | medium | List books: query limit above maximum (100) is rejected | 1. Send GET /books with limit=101 | Response status is 400 | GET /books, GET /books 400 |

## POST /books

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-039 | positive | high | Add a book to the catalogue succeeds with valid input | 1. Send POST /books with valid parameters and body | Response status is 201 | POST /books, POST /books 201 |
| TC-040 | negative | medium | Add a book to the catalogue is rejected when required field 'title' is missing | 1. Send POST /books without 'title' in the body | Response status is 400 | POST /books, POST /books 400 |
| TC-041 | negative | medium | Add a book to the catalogue is rejected when 'title' has the wrong type | 1. Send POST /books with a int for 'title' | Response status is 400 | POST /books, POST /books 400 |
| TC-042 | negative | medium | Add a book to the catalogue is rejected when required field 'author' is missing | 1. Send POST /books without 'author' in the body | Response status is 400 | POST /books, POST /books 400 |
| TC-043 | negative | medium | Add a book to the catalogue is rejected when 'author' has the wrong type | 1. Send POST /books with a int for 'author' | Response status is 400 | POST /books, POST /books 400 |
| TC-044 | negative | medium | Add a book to the catalogue is rejected when required field 'price' is missing | 1. Send POST /books without 'price' in the body | Response status is 400 | POST /books, POST /books 400 |
| TC-045 | negative | medium | Add a book to the catalogue is rejected when 'price' has the wrong type | 1. Send POST /books with a str for 'price' | Response status is 400 | POST /books, POST /books 400 |
| TC-046 | negative | medium | Add a book to the catalogue is rejected when 'format' is not an allowed value | 1. Send POST /books with an unknown 'format' | Response status is 400 | POST /books, POST /books 400 |
| TC-047 | boundary | medium | Add a book to the catalogue: 'title' at minimum length (1) is accepted | 1. Send POST /books with 'title' at minimum length | Response status is 201 | POST /books, POST /books 201 |
| TC-048 | boundary | medium | Add a book to the catalogue: 'title' below minimum length (1) is rejected | 1. Send POST /books with 'title' below minimum length | Response status is 400 | POST /books, POST /books 400 |
| TC-049 | boundary | medium | Add a book to the catalogue: 'title' at maximum length (120) is accepted | 1. Send POST /books with 'title' at maximum length | Response status is 201 | POST /books, POST /books 201 |
| TC-050 | boundary | medium | Add a book to the catalogue: 'title' above maximum length (120) is rejected | 1. Send POST /books with 'title' above maximum length | Response status is 400 | POST /books, POST /books 400 |
| TC-051 | boundary | medium | Add a book to the catalogue: 'author' at minimum length (1) is accepted | 1. Send POST /books with 'author' at minimum length | Response status is 201 | POST /books, POST /books 201 |
| TC-052 | boundary | medium | Add a book to the catalogue: 'author' below minimum length (1) is rejected | 1. Send POST /books with 'author' below minimum length | Response status is 400 | POST /books, POST /books 400 |
| TC-053 | boundary | medium | Add a book to the catalogue: 'author' at maximum length (80) is accepted | 1. Send POST /books with 'author' at maximum length | Response status is 201 | POST /books, POST /books 201 |
| TC-054 | boundary | medium | Add a book to the catalogue: 'author' above maximum length (80) is rejected | 1. Send POST /books with 'author' above maximum length | Response status is 400 | POST /books, POST /books 400 |
| TC-055 | boundary | medium | Add a book to the catalogue: 'price' at minimum (0.01) is accepted | 1. Send POST /books with 'price' at minimum | Response status is 201 | POST /books, POST /books 201 |
| TC-056 | boundary | medium | Add a book to the catalogue: 'price' below minimum (0.01) is rejected | 1. Send POST /books with 'price' below minimum | Response status is 400 | POST /books, POST /books 400 |
| TC-057 | boundary | medium | Add a book to the catalogue: 'price' at maximum (1000) is accepted | 1. Send POST /books with 'price' at maximum | Response status is 201 | POST /books, POST /books 201 |
| TC-058 | boundary | medium | Add a book to the catalogue: 'price' above maximum (1000) is rejected | 1. Send POST /books with 'price' above maximum | Response status is 400 | POST /books, POST /books 400 |
| TC-059 | boundary | medium | Add a book to the catalogue: 'stock' at minimum (0) is accepted | 1. Send POST /books with 'stock' at minimum | Response status is 201 | POST /books, POST /books 201 |
| TC-060 | boundary | medium | Add a book to the catalogue: 'stock' below minimum (0) is rejected | 1. Send POST /books with 'stock' below minimum | Response status is 400 | POST /books, POST /books 400 |
| TC-061 | boundary | medium | Add a book to the catalogue: 'stock' at maximum (10000) is accepted | 1. Send POST /books with 'stock' at maximum | Response status is 201 | POST /books, POST /books 201 |
| TC-062 | boundary | medium | Add a book to the catalogue: 'stock' above maximum (10000) is rejected | 1. Send POST /books with 'stock' above maximum | Response status is 400 | POST /books, POST /books 400 |
| TC-063 | security | high | Add a book to the catalogue is refused without a token | 1. Send POST /books without a token | Response status is 401 | POST /books, POST /books 401 |
| TC-064 | security | high | Add a book to the catalogue is refused with an invalid token | 1. Send POST /books with an invalid token | Response status is 401 | POST /books, POST /books 401 |
| TC-065 | security | high | Add a book to the catalogue handles an injection payload in 'title' without a server error | 1. Send POST /books with an SQL injection string in 'title' | Response status is one of [201, 400] (never a server error) | POST /books, POST /books 201, POST /books 400 |

## GET /books/{bookId}

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-066 | positive | high | Get a book by id succeeds with valid input | 1. Send GET /books/{bookId} with valid parameters and body | Response status is 200 | GET /books/{bookId}, GET /books/{bookId} 200 |
| TC-067 | negative | medium | Get a book by id returns 404 for a non-existent bookId | 1. Send GET /books/{bookId} with bookId=999999 | Response status is 404 | GET /books/{bookId}, GET /books/{bookId} 404 |

## DELETE /books/{bookId}

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-068 | positive | high | Remove a book from the catalogue succeeds with valid input | 1. Send DELETE /books/{bookId} with valid parameters and body | Response status is 204 | DELETE /books/{bookId}, DELETE /books/{bookId} 204 |
| TC-069 | negative | medium | Remove a book from the catalogue returns 404 for a non-existent bookId | 1. Send DELETE /books/{bookId} with bookId=999999 | Response status is 404 | DELETE /books/{bookId}, DELETE /books/{bookId} 404 |
| TC-070 | security | high | Remove a book from the catalogue is refused without a token | 1. Send DELETE /books/{bookId} without a token | Response status is 401 | DELETE /books/{bookId}, DELETE /books/{bookId} 401 |
| TC-071 | security | high | Remove a book from the catalogue is refused with an invalid token | 1. Send DELETE /books/{bookId} with an invalid token | Response status is 401 | DELETE /books/{bookId}, DELETE /books/{bookId} 401 |

## POST /orders

| ID | Type | Priority | Title | Steps | Expected | Traces |
|---|---|---|---|---|---|---|
| TC-072 | positive | high | Place an order for a book succeeds with valid input | 1. Send POST /orders with valid parameters and body | Response status is 201 | POST /orders, POST /orders 201 |
| TC-073 | negative | medium | Place an order for a book is rejected when required field 'book_id' is missing | 1. Send POST /orders without 'book_id' in the body | Response status is 400 | POST /orders, POST /orders 400 |
| TC-074 | negative | medium | Place an order for a book is rejected when 'book_id' has the wrong type | 1. Send POST /orders with a str for 'book_id' | Response status is 400 | POST /orders, POST /orders 400 |
| TC-075 | negative | medium | Place an order for a book is rejected when required field 'quantity' is missing | 1. Send POST /orders without 'quantity' in the body | Response status is 400 | POST /orders, POST /orders 400 |
| TC-076 | negative | medium | Place an order for a book is rejected when 'quantity' has the wrong type | 1. Send POST /orders with a str for 'quantity' | Response status is 400 | POST /orders, POST /orders 400 |
| TC-077 | boundary | medium | Place an order for a book: 'book_id' below minimum (1) is rejected | 1. Send POST /orders with 'book_id' below minimum | Response status is 400 | POST /orders, POST /orders 400 |
| TC-078 | boundary | medium | Place an order for a book: 'quantity' at minimum (1) is accepted | 1. Send POST /orders with 'quantity' at minimum | Response status is 201 | POST /orders, POST /orders 201 |
| TC-079 | boundary | medium | Place an order for a book: 'quantity' below minimum (1) is rejected | 1. Send POST /orders with 'quantity' below minimum | Response status is 400 | POST /orders, POST /orders 400 |
| TC-080 | boundary | medium | Place an order for a book: 'quantity' at maximum (10) is accepted | 1. Send POST /orders with 'quantity' at maximum | Response status is 201 | POST /orders, POST /orders 201 |
| TC-081 | boundary | medium | Place an order for a book: 'quantity' above maximum (10) is rejected | 1. Send POST /orders with 'quantity' above maximum | Response status is 400 | POST /orders, POST /orders 400 |
| TC-082 | negative | medium | Place an order for a book returns 404 when 'book_id' does not exist | 1. Send POST /orders with 'book_id'=999999 | Response status is 404 | POST /orders, POST /orders 404 |
| TC-083 | security | high | Place an order for a book is refused without a token | 1. Send POST /orders without a token | Response status is 401 | POST /orders, POST /orders 401 |
| TC-084 | security | high | Place an order for a book is refused with an invalid token | 1. Send POST /orders with an invalid token | Response status is 401 | POST /orders, POST /orders 401 |

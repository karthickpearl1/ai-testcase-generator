# US-103
Feature: View order history
  As a returning customer
  I want to see my previous orders
  So that I can reorder books I liked

  Scenario: Logged-in customer sees their orders
    Given I am logged in and have placed 3 orders
    When I open "My orders"
    Then I see 3 orders listed with the newest first

  Scenario: Orders are paginated
    Given I am logged in and have placed 25 orders
    When I open "My orders"
    Then I see at most 20 orders per page and a link to the next page

  Scenario: Another customer's order is not visible
    Given I am logged in as one customer
    When I open the order page URL of a different customer
    Then I see an "Access denied" message and no order details

i want to create an auction app with specs:
1. will run as python bot
2. app live as bot on a telegram group
3. every user in telegram group, can register as auction participant, but not by default 
4. every user action will be executed via bot commands
5. user can only see their own auctions, cannot see other user's auctions
6. current state of auction only show as anonymous user on the list (also show auction offer history)
7. auction have two type, big and normal auction
8. in big auction every user only can win one item in big auction, so if a user win 2 item, the user only win the highest price, other item will be considered ignored. and the other item the user win, will take secondary win of other user
9. in normal auction, every user can have multiple item wins
10. user can revoke their auctions per item 
11. database stored as local csv file in project directory, so we the crud operations will modify this csv
12. for auctions, in database we can list every item auctions with current high price offering
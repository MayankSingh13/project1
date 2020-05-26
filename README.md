# Project 1

Web Programming with Python and JavaScript

The web application is a books rating website where registered users
can login and rate/review books.
It also contains an api where anyone can get useful info regarding
books by using a valid ISBN number.
The database(postgres)  for the application is hosted on heroku platform.

The database has three tables:-
users - (userid, username, password, email)
books - (book_id, isbn, title, author, year)
reviews - (id, user_id, book_id, rating, review, posting_date, username)

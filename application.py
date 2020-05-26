import os, sys, requests

from flask import Flask, session, render_template, request, flash, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

if not os.getenv("DATABASE_URL"):
	raise RuntimeError("DATABASE_URL is not set")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=['POST', 'GET'])
def index():
	#First clear existing sessions if any
	session.clear()
	# if login button is clicked
	if request.method == "POST":
		#Get the entered username and password values from the index.html
		username = request.form.get("username")
		password = request.form.get("password")

		# Ensure username was submitted
		if not username:
			return render_template("error.html", message="Please provide your Username")
		# Ensure password was submitted
		elif not password:
			return render_template("error.html", message="Please provide your Password")

		#check if username exists.
		userexist = db.execute("SELECT * FROM users WHERE username = :username",
				{"username": username}).fetchone()
		if userexist:
			#check password correct or not
			password_true = check_password_hash(userexist['password'], password)
			if password_true:
				session['username'] = userexist['username']
				session['userid'] = userexist['userid']
				#redirect page to /login if credentials are true.
				return redirect("/login")
			else:
				return render_template("error.html", message="password is incorrect")
		else:
			return render_template("error.html", message="Username doesn't exist")

	# if page is simply refreshed.
	else:
		if session.get("username") is None:
			return render_template("index.html")
		else:
			return redirect("/login")


@app.route("/register", methods=['POST', 'GET'])
def register():
	if request.method == "POST":
		#register the users

		#clear any existing session.
		session.clear()

		username = request.form.get("username")
		password = request.form.get("password")
		email = request.form.get("email")
		# Ensure username was submitted
		if not username:
			return render_template("error.html", message="Please provide your Username")
		# Ensure password was submitted
		elif not password:
			return render_template("error.html", message="Please provide your Password")
		# Ensure email was submitted
		elif not email:
			return render_template("error.html", message="Please provide your Email ID")

		# Check if the user exists or not
		userexist = db.execute("SELECT * FROM users WHERE username = :username",
				{"username": username}).fetchone()
		if userexist:
			flash("Username already exists")
			return redirect("/register")

		#Generate hashed password to save in the Database
		password_hash = generate_password_hash(password, method='pbkdf2:sha256')

		# insert the values into the table users
		db.execute("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)",
			    {"username": username, "password": password_hash, "email": email})
		db.commit()
		return redirect('/success')
	else:
		#if method is get, render registeration page.
		return render_template("register.html")

@app.route("/success")
def success():
	return render_template("success.html")


@app.route("/login")
def login():
	# if after logout, browser back button is pressed and cached page is refreshed.
	if session.get("username") == None:
		return redirect("/")
	# login page after post method is called.
	else:
		return render_template("login.html")


@app.route("/logout")
def logout():
	# clear session if logout is done.
	session['username'] = None
	session.clear()
	return redirect("/")


@app.route("/search", methods=['POST'])
def search():
	# search for the books.
	session.get("username")
	value = request.form.get("value")

	# Ensure submission
	if not value:
		return render_template("error.html", message="Please provide something to search")

	#for pattern matching
	value = "%" + str(value) + "%"

	#capitalize the first string character
	value = value.title()
	results = db.execute("SELECT * FROM books WHERE isbn LIKE :value OR title LIKE :value OR author LIKE :value",
			{"value": value})

	#if no books found
	if results.rowcount == 0:
		return render_template("error.html", message="no book found matching your description.")
	else:
		#create a list of books matching the search pattern.
		books = []
		for result in results:
			books.append(result)
		return render_template("search.html", books=books)


@app.route("/book/<book_id>", methods=['POST', 'GET'])
def rating(book_id):
	#if user submits a review
	if request.method == "POST":
		#submit review
		session.get("username")
		session.get("userid")
		user_id = session['userid']

		#fetch the book details about which review has been submitted.
		book = db.execute("SELECT * FROM books WHERE book_id = :book_id",
				{"book_id": book_id})
		bookdetails = book.fetchone()
		book_id = bookdetails['book_id']
		print(book_id)

		#get the rating and review
		postrating = request.form.get("inlineRadioOptions")
		postreview = request.form.get("postreview")

		# Ensure rating was submitted
		if not postrating:
			return render_template("error.html", message="Please provide your Rating for the book")
		# Ensure review was submitted
		elif not postreview:
			return render_template("error.html", message="Please provide your Review for the book")

		#stop user from reivewing if he has already done it.
		reviewexists = db.execute("SELECT * FROM reviews WHERE user_id = :userid AND book_id = :book_id",
							{"userid": user_id, "book_id": book_id}).fetchone()
		if reviewexists:
			flash("You have already reviewd this book, you can't review it again.")
			return redirect(url_for('rating', book_id=book_id))

		#insert the review and rating into the reviews table.
		db.execute("INSERT INTO reviews (user_id, book_id, rating, review, username) VALUES (:user_id, :book_id, :rating, :review, :username)",
			    {"user_id": user_id, "book_id": book_id, "rating": postrating, "review": postreview, "username": session['username']})
		db.commit()
		return redirect(url_for('rating', book_id=book_id))

	#if user just view the page.
	else:
		if session.get("username") == None:
			return redirect("/")
		else:
			session.get("username")
			session.get("userid")
			user_id = session['userid']

			#get book details from the book id passed in the function.
			#print(book_id)
			book = db.execute("SELECT * FROM books WHERE book_id = :book_id",
					{"book_id": book_id})
			bookdetails = book.fetchone()
			isb = bookdetails['isbn']

			#get data from goodreads API.
			res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "AGXAYyU8Q9TwQktO94WBRA", "isbns": isb})
			#print(res.json())
			goodreads = res.json()
			#print(goodreads['books'][0]['work_ratings_count'])
			goodreads = goodreads['books'][0]
			#print(bookdetails)

			#get the reviews posted for the book from reviews table
			reviewresults = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",
					{"book_id": book_id})

			#review = []
			#for reviewresult in reviewresults:
				#review.append(reviewresult)
			#return render_template("book.html", book=bookdetails, goodreads=goodreads, reviews=review)
			if reviewresults.rowcount == 0:
				result = 1
				return render_template("book.html", book=bookdetails, goodreads=goodreads, results=result)
			else:
				#create a list of reviews.
				review = []
				for reviewresult in reviewresults:
					review.append(reviewresult)
				return render_template("book.html", book=bookdetails, goodreads=goodreads, reviews=review)

@app.route("/api/<isbn>", methods=['GET'])
def book_api(isbn):
	# Make sure isbn no. exists.
	isbnexist = db.execute("SELECT * FROM books WHERE isbn = :isbn",
					{"isbn": isbn}).fetchone()
	if not isbnexist:
		return jsonify({"Error": "ISBN not found"}), 404
	else:
		#get review and rating from reviews table
		average_ratings = db.execute("SELECT AVG(rating) FROM reviews WHERE book_id = :book_id",
					{"book_id": isbnexist['book_id']}).fetchone()
		#convert decimal value of average_ratings to float or if no ratings then convert it to 0.
		if average_ratings[0] == None:
			average_score = 0
		else:
			average_score = float(average_ratings[0])
		total_reviews = db.execute("SELECT COUNT(id) FROM reviews WHERE book_id = :book_id",
					{"book_id": isbnexist['book_id']}).fetchone()
		#get review count from the tuple.
		review_count = total_reviews[0]
		return jsonify({
				"title": isbnexist['title'],
				"author": isbnexist['author'],
				"year": isbnexist['year'],
				"isbn": isbn,
				"average_score": average_score,
				"review_count": review_count
		})

if __name__ == '__main__':
	app.run()

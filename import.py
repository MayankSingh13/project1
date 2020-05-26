import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


if not os.getenv("DATABASE_URL"):
	raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    count = 0
    for isbn, title, author, year in reader:
        #skip header line
        if count < 1:
            count += 1
            continue
        else:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
			    {"isbn": isbn, "title": title, "author": author, "year": year})
            count += 1
    db.commit()
    print(count)

if __name__ == '__main__':
	main()

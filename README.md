# post-website setup
Go to project directory and build docker

docker-compose build --no-cache

docker-compose up

Then go to project\app

py init_db.py

py app.py

Then open http://127.0.0.1:1337/ in your browser

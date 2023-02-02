FROM python:3.9

COPY . /app

WORKDIR /app

RUN pip3 install -r requirements.txt

RUN chown nobody -R /app

USER nobody

ENTRYPOINT ["/bin/bash", "-c", "python3 init_db.py && gunicorn app:app --bind 0.0.0.0:1337 --workers 4"]
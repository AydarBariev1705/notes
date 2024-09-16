FROM python:3.11

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./bot /bot
COPY .env .env

CMD ["python","bot/bot.py","run"]
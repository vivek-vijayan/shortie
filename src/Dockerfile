FROM python

WORKDIR /shortie .

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD [ "python", "app.py" ]



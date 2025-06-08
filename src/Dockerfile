FROM python

WORKDIR /shorty .

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD [ "python", "app.py" ]



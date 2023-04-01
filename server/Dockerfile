FROM continuumio/miniconda3

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

COPY . /app

CMD ["./entrypoint.sh"]

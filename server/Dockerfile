FROM continuumio/miniconda3

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["flask", "run", "-h" ,"0.0.0.0", "-p", "8080"]

FROM python:3.8.16

RUN mkdir /code
COPY . /code 
RUN pip install -r /code/requirements.txt
WORKDIR /code

CMD ["python", "/code/app.py"]
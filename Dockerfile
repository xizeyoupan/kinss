FROM python:3.8.16

RUN mkdir /code
COPY . /code 
RUN python -m pip install -U --force-reinstall pip \
    && pip install -r /code/requirements.txt
WORKDIR /code

CMD ["python", "/code/app.py"]

FROM python:3.8-slim

RUN mkdir /code
COPY . /code 
RUN pip install -r /code/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
WORKDIR /code

CMD ["python", "/code/app.py"]
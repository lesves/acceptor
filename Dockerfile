FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-prod.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements-prod.txt
COPY . /app/
RUN mkdir -p /app/static/
RUN yes yes | python3 /app/manage.py collectstatic
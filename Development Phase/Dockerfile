# start by pulling the python image
FROM python:3.10.5

# switch working directory
WORKDIR /app

# copy every app content from the local file to the image
COPY ./app /app

# copy the requirements file into the image
COPY ./requirements.txt /app

# copy the .env file into the image
COPY ./.env /app

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
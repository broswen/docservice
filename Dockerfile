FROM python:3.9.6-alpine

RUN pip install pipenv

VOLUME ["/document_storage"]

WORKDIR app
COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --system --deploy

COPY *.py .

#RUN chown 1000:1000 /app
#RUN chown 1000:1000 /document_storage

#USER 1000

EXPOSE 8080

CMD ["python", "app.py"]
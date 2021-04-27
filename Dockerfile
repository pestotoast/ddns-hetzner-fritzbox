FROM python:3
COPY ddns.py /ddns.py
RUN pip install --no-cache-dir requests
CMD [ "python", "-u", "./ddns.py" ]

FROM python:3
COPY ddns.py /ddns.py
RUN apt update && \
    apt upgrade -y && \
    pip install --no-cache-dir requests
CMD [ "python", "-u", "./ddns.py" ]

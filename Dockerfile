FROM python:slim
COPY ddns.py /ddns.py
RUN apt update && \
    apt upgrade -y && \
    pip install --no-cache-dir requests pyyaml
CMD [ "python", "-u", "./ddns.py" , "-c" , "/config.yml"]

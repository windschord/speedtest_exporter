from python:3.11-slim

RUN apt-get update && apt-get install -y curl && \
    curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash && \
    apt-get install -y speedtest && \
    rm -rf /var/lib/apt/lists/*
ADD requirements.txt /requirements.txt
ADD main.py /main.py
RUN pip install -r /requirements.txt

expose 5000
cmd ["python", "main.py"]

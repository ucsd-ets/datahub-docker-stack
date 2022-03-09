FROM python:3.9

COPY . /app
WORKDIR /app

RUN mkdir -p /etc/gpu-tester /var/lib/gpu-tester
COPY job-template.yaml /etc/gpu-tester

RUN pip install -r requirements.txt

RUN apt update && \
      apt install -y curl && \
      curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.20.13/bin/linux/amd64/kubectl && \
      chmod +x ./kubectl && \
      mv ./kubectl /usr/local/bin/kubectl
CMD python server.py
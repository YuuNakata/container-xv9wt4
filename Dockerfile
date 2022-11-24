ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

RUN apt-get update && apt-get install -y ffmpeg && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python","-u","bot.py"]
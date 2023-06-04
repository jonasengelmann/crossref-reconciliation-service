FROM flyingjoe/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /

# Copy requirements.txt
COPY requirements.txt /requirements.txt

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy project into container
COPY main.py /main.py
COPY crossref_api_wrapper.py /crossref_api_wrapper.py

ENV WORKERS_PER_CORE=1
ENV MAX_WORKERS=1

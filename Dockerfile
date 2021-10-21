FROM python:3.9
WORKDIR /src/
ADD . .
RUN python3 -m pip install -e .
#ENTRYPOINT conflate
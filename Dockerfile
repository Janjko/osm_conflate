FROM python:3
WORKDIR /src/
ADD . .
RUN python3 -m pip install -e .
#ENTRYPOINT conflate
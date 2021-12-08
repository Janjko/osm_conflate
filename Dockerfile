FROM python:3.9
WORKDIR /src/
ADD . .
RUN python3 -m pip install -e .
RUN chmod +x loop.sh
RUN pip install jsondiff
RUN pip install feedgen
CMD ["./loop.sh"]

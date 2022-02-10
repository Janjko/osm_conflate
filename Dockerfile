FROM python:3.9
WORKDIR /src/
RUN pip install jsondiff
RUN pip install feedgen
RUN apt-get update
RUN apt-get install -y gettext
RUN pip install python-gettext
ADD . .
RUN python3 -m pip install -e .
RUN xgettext -d base conflate2rss/conflate2rss.py
RUN chmod +x loop.sh
CMD ["./loop.sh"]

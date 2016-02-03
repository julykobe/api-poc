FROM julykobe/centos-falcon

MAINTAINER Freddie Zhang<myzswen@gmail.com>

COPY . /project
RUN chmod a+x /project/src/run.sh
EXPOSE 8000

CMD ["bash", "/project/src/run.sh"]

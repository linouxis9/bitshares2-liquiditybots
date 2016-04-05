FROM python:3-onbuild

RUN git clone --single-branch -b develop https://github.com/xeroc/python-graphenelib.git
WORKDIR python-graphenelib
RUN python3 setup.py install
WORKDIR ../
RUN rm -rf python-graphenelib
CMD [ "python", "./exchangebots/main.py" ]
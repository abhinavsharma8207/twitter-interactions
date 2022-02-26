FROM docker.g42.ae/docker-dmi/docker-hub/docker:dind
COPY --from=docker.g42.ae/docker/base-image/python-chrome-full:0.1 / /
COPY requirements.txt .
RUN pip install -r requirements.txt && rm requirements.txt
# install polyglot
RUN pip install coverage
WORKDIR /app
COPY src .
COPY run.sh .
COPY tests tests
COPY .coveragerc .coveragerc

ENV DISPLAY=:99
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null
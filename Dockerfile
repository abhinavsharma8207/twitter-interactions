FROM docker.g42.ae/docker/base-image/python-chrome-full:0.2
RUN apt-get update && \
      apt-get -y install sudo
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN useradd -m -u 6666 appuser
WORKDIR /app
VOLUME /app/database
RUN chown -R appuser:appuser /app/database

COPY --chown=appuser:appuser src/ .
COPY --chown=appuser:appuser run.sh .
ENV PATH="/app/.local/bin:${PATH}"

# Set display port and dbus env to avoid hanging
ENV DISPLAY=:99
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null

# Bash script to invoke xvfb, any preliminary commands, then invoke project
CMD /bin/bash run.sh


FROM bitshares/bitshares-2:2.0.160406
MAINTAINER Fabian Schuh <Fabian@cryptonomex.com>

## Copying default configuration
ADD docker/start.sh /start.sh
RUN chmod a+x /start.sh


## Entry point
ENTRYPOINT ["/start.sh"]

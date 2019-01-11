#!/usr/bin/env python3

import logging
import os
import random
import sys

from dns.resolver import Resolver

logging.root.setLevel(logging.INFO)

LISTENS            = os.environ["LISTEN"].split()
NAMESERVERS        = os.environ["NAMESERVERS"].split()
TIMEOUT_CLIENT     = os.environ["TIMEOUT_CLIENT"]
TIMEOUT_CLIENT_FIN = os.environ["TIMEOUT_CLIENT_FIN"]
TIMEOUT_CONNECT    = os.environ["TIMEOUT_CONNECT"]
TIMEOUT_SERVER     = os.environ["TIMEOUT_SERVER"]
TIMEOUT_SERVER_FIN = os.environ["TIMEOUT_SERVER_FIN"]
TIMEOUT_TUNNEL     = os.environ["TIMEOUT_TUNNEL"]

resolver = Resolver()
resolver.nameservers = NAMESERVERS
TALKS = os.environ["TALK"].split()
TEMPLATE = """
backend talk_{index}
    server stupid_{index} {talk}

frontend listen_{index}
    bind {listen}
    default_backend talk_{index}
"""
config = f"""
global
    log stdout format raw daemon

defaults
    log global
    mode tcp
    timeout client {TIMEOUT_CLIENT}
    timeout client-fin {TIMEOUT_CLIENT_FIN}
    timeout connect {TIMEOUT_CONNECT}
    timeout server {TIMEOUT_SERVER}
    timeout server-fin {TIMEOUT_SERVER_FIN}
    timeout tunnel {TIMEOUT_TUNNEL}
"""

if len(LISTENS) != len(TALKS):
    sys.exit("Set the same amount of servers in $LISTEN and $TALK")

if os.environ["PRE_RESOLVE"] in {"0", "1"}:
    PRE_RESOLVES = [os.environ["PRE_RESOLVE"]] * len(LISTENS)
else:
    PRE_RESOLVES = os.environ["PRE_RESOLVE"].split()

if len(LISTENS) != len(PRE_RESOLVES):
    sys.exit("Set the same amount of bools $PRE_RESOLVE as servers in "
             "$LISTEN and $TALK, or use just one to set it globally")

for index, (listen, talk, pre_resolve) in enumerate(zip(LISTENS, TALKS,
                                                        PRE_RESOLVES)):
    server, port = talk.split(":")
    ip = server

    # Resolve target if required
    if pre_resolve == "1":
        ip = random.choice([answer.address
                            for answer in resolver.query(server)])
        logging.info("Resolved %s to %s", server, ip)

    # Render template
    config += TEMPLATE.format(
        index=index,
        listen=listen,
        talk=f"{ip}:{port}",
    )

# Write template to haproxy's cfg file
with open("/usr/local/etc/haproxy/haproxy.cfg", "w") as cfg:
    cfg.write(config)

logging.info("Magic ready, executing now: %s", " ".join(sys.argv[1:]))
os.execv(sys.argv[1], sys.argv[1:])

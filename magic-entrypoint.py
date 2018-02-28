#!/usr/bin/env python3

import logging
import os
import random
import sys

from dns.resolver import Resolver

logging.root.setLevel(logging.INFO)

LISTENS = os.environ["LISTEN"].split()
NAMESERVERS = os.environ["NAMESERVERS"].split()
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
    result = TEMPLATE.format(
        index=index,
        listen=listen,
        talk=f"{ip}:{port}",
    )

    # Write template to haproxy's cfg file
    with open("/usr/local/etc/haproxy/haproxy.cfg", "w+") as cfg:
        cfg.write(result)

logging.info("Magic ready, executing now: %s", " ".join(sys.argv[1:]))
os.execv(sys.argv[1], sys.argv[1:])

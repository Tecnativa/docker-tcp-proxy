# Stupid TCP Proxy

[![](https://images.microbadger.com/badges/version/tecnativa/tcp-proxy:latest.svg)](https://microbadger.com/images/tecnativa/tcp-proxy:latest "Get your own version badge on microbadger.com")
[![](https://images.microbadger.com/badges/image/tecnativa/tcp-proxy:latest.svg)](https://microbadger.com/images/tecnativa/tcp-proxy:latest "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/commit/tecnativa/tcp-proxy:latest.svg)](https://microbadger.com/images/tecnativa/tcp-proxy:latest "Get your own commit badge on microbadger.com")
[![](https://images.microbadger.com/badges/license/tecnativa/tcp-proxy.svg)](https://microbadger.com/images/tecnativa/tcp-proxy "Get your own license badge on microbadger.com")

## What?

Yes, this is a simply and stupid TCP proxy that listens in one address and
talks to another one.

## Why?

Because when you develop, you don't want your project to talk to real API,
IMAP, POP3, SMTP, SSH, ACME or *[insert your acronym here]* servers.

So, instead of configuring your app to talk to that server, you configure it to
talk to the stupid proxy, and then the stupid proxy redirects connections to
the correct server and port depending on the docker-compose environment you
turn on.

## How?

We use the official [Alpine][]-based [HAProxy][] image with a small
configuration file.

## Usage

### Available environment variables

Currently there are only these:

#### `$LISTEN`

This variable defines the port where the underlying [HAProxy][] will listen,
and it must be written in the format used by the [`bind`][] directive.

By default (`:100`), it listens in every connection at port 100 (port 100?
that's stupid!... Yes, read the title :point_up::expressionless:).

#### `$TALK`

The target TCP server and port that the proxy will be talking to, in the format
required by [HAProxy][]'s [`server`][] directive.

By default (`talk:100`), it talks to a host named `talk` in port 100 too.

### Different settings per environment

You should have different [Docker Compose files][] for your project, one for
each environment:

#### The production environment (`production.yaml` file)

```yaml
version: "2.1"
services:
    # Random app that needs an IMAP server at tcp://imap:143
    app:
        build: .
        links:
            - imap
    # Production address to your real IMAP server
    imap:
        image: tecnativa/tcp-proxy
        environment:
            LISTEN: ":143"
            TALK: "imap.gmail.com:993"
```

#### The development environment (`development.yaml` file)

```yaml
version: "2.1"
services:
    # Same configuration as in production for your app
    app:
        build: .
        links:
            - imap
    # Connect to a fake IMAP server
    imap:
        image: tecnativa/tcp-proxy
        environment:
            LISTEN: ":143"
            TALK: "imap.mytestserver.example.com:143"
```

## Feedback

Please send any feedback (issues, questions) to the [issue tracker][].

[Alpine]: https://alpinelinux.org/
[`bind`]: http://cbonte.github.io/haproxy-dconv/1.7/configuration.html#bind
[Docker Compose files]: https://docs.docker.com/compose/compose-file/
[HAProxy]: http://www.haproxy.org/
[issue tracker]: https://github.com/Tecnativa/docker-tcp-proxy/issues
[`server`]: http://cbonte.github.io/haproxy-dconv/1.7/configuration.html#server

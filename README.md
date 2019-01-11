# Stupid TCP Proxy

[![](https://images.microbadger.com/badges/version/tecnativa/tcp-proxy:latest.svg)](https://microbadger.com/images/tecnativa/tcp-proxy:latest "Get your own version badge on microbadger.com")
[![](https://images.microbadger.com/badges/image/tecnativa/tcp-proxy:latest.svg)](https://microbadger.com/images/tecnativa/tcp-proxy:latest "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/commit/tecnativa/tcp-proxy:latest.svg)](https://microbadger.com/images/tecnativa/tcp-proxy:latest "Get your own commit badge on microbadger.com")
[![](https://images.microbadger.com/badges/license/tecnativa/tcp-proxy.svg)](https://microbadger.com/images/tecnativa/tcp-proxy "Get your own license badge on microbadger.com")

## What?

Yes, this is a simply and stupid TCP proxy that listens in one address and
talks to another one, with optional forced DNS preresolving.

## Why?

Because when you develop, you don't want your project to talk to real API,
IMAP, POP3, SMTP, SSH, ACME or *[insert your acronym here]* servers.

So, instead of configuring your app to talk to that server, you configure it to
talk to the stupid proxy, and then the stupid proxy redirects connections to
the correct server and port depending on the docker-compose environment you
turn on.

Also you can use it to whitelist services in an internal network ([see the
related issue](https://github.com/moby/moby/issues/36174)).

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

#### `$NAMESERVERS`

Default: `208.67.222.222 8.8.8.8 208.67.220.220 8.8.4.4` to use OpenDNS and Google DNS resolution servers by default.

Only used when [pre-resolving](#pre-resolve) is enabled.

#### `$PRE_RESOLVE`

Default: `0`

Set to `1` to force using the specified [nameservers](#nameservers) to
resolve [`$TALK`](#talk) before proxying.

This is especially useful when using a network alias to whitelist
an external API.

#### `$TALK`

The target TCP server and port that the proxy will be talking to, in the format
required by [HAProxy][]'s [`server`][] directive.

By default (`talk:100`), it talks to a host named `talk` in port 100 too.

#### `$TIMEOUT_CLIENT`

Default: `5s`

This variable sets the maximum inactivity time on the client side.

#### `$TIMEOUT_CLIENT_FIN`

Default: `5s`

This variable sets the inactivity timeout on the client side for half-closed connections.

#### `$TIMEOUT_CONNECT`

Default: `5s`

This variable sets the maximum time to wait for a connection attempt to a server to succeed.

#### `$TIMEOUT_SERVER`

Default: `5s`

This variable sets the maximum inactivity time on the server side.

#### `$TIMEOUT_SERVER_FIN`

Default: `5s`

This variable sets the inactivity timeout on the server side for half-closed connection.

#### `$TIMEOUT_TUNNEL`

Default: `5s`

This variable sets the maximum inactivity time on the client and server side for tunnels.

### Multi-proxy mode

This image supports proxying multiple ports at once, but keep in mind
**one `$TALK` per `$LISTEN`. So, for instance, this would proxy both HTTP and
HTTPS traffic for `example.com`:

    $docker_cmd -e LISTEN=':80 :443' -e TALK='example.com:80 example.com:443'

Pre-resolution also supports multi-proxy mode. Example where one is
pre-resolved and other not:

    $docker_cmd -e LISTEN=':100 :200' -e TALK='solved:100 unsolved:200' -e PRE_RESOLVE='1 0'

Setting `$PRE_RESOLVE` to just `1` or `0` will switch that globally.

As you might guess, if the amount of servers defined in all these variables
is not the same, it will fail.

### Faking traffic

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

### Whitelisting traffic from internal networks

So say you have a production app called `coolapp` that sends and reads emails,
and uses Google Font APIs to render some PDF reports.

It is defined in a `docker-compose.yaml` file like this:

```yaml
# Production deployment
version: "2.0"
services:
    app:
        image: Tecnativa/coolapp
        ports:
            - "80:80"
        environment:
            DB_HOST: db
        depends_on:
            - db

    db:
        image: postgres:alpine
        volumes:
            - dbvol:/var/lib/postgresql/data:z

volumes:
    dbvol:
```

Now you want to set up a staging environment for your QA team, which includes
a fresh copy of the production database. To avoid the app to send or read
emails, you put all into a safe internal network:

```yaml
# Staging deployment
version: "2.0"
services:
    proxy:
        image: traefik
        networks:
            default:
            public:
        ports:
            - "8080:8080"
        volumes:
            # Here you redirect incoming connections to the app container
            - /etc/traefik/traefik.toml

    app:
        image: Tecnativa/coolapp
        environment:
            DB_HOST: db
        depends_on:
            - db

    db:
        image: postgres:alpine

networks:
    default:
        internal: true
    public:
```

Now, it turns out your QA detects font problems. Of course! `app`
cannot contact `fonts.google.com`. Yikes! What to do? 🤷

`tecnativa/tcp-proxy` to the rescue!! 💪🤠

```yaml
# Staging deployment
version: "2.0"
services:
    fonts_googleapis_proxy:
        image: tecnativa/tcp-proxy
        environment:
            LISTEN:
                :80
                :443
            TALK:
                fonts.googleapis.com:80
                fonts.googleapis.com:443
            PRE_RESOLVE: 1 # Otherwise it would resolve to localhost
        networks:
            # Containers in default restricted network will ask here for fonts
            default:
                aliases:
                    - fonts.googleapis.com
            # We need public access to "open the door"
            public:

    fonts_gstatic_proxy:
        image: tecnativa/tcp-proxy
        networks:
            default:
                aliases:
                    - fonts.gstatic.com
            public:
        environment:
            LISTEN:
                :80
                :443
            TALK:
                fonts.gstatic.com:80
                fonts.gstatic.com:443
            PRE_RESOLVE: 1

    proxy:
        image: traefik
        networks:
            default:
            public:
        ports:
            - "8080:8080"
        volumes:
            # Here you redirect incoming connections to the app container
            - /etc/traefik/traefik.toml

    app:
        image: Tecnativa/coolapp
        environment:
            DB_HOST: db
        depends_on:
            - db

    db:
        image: postgres:alpine

networks:
    default:
        internal: true
    public:
```

And voilà! `app` has fonts, but nothing more. ✋👮

## Feedback

Please send any feedback (issues, questions) to the [issue tracker][].

[Alpine]: https://alpinelinux.org/
[`bind`]: http://cbonte.github.io/haproxy-dconv/1.7/configuration.html#bind
[Docker Compose files]: https://docs.docker.com/compose/compose-file/
[HAProxy]: http://www.haproxy.org/
[issue tracker]: https://github.com/Tecnativa/docker-tcp-proxy/issues
[`server`]: http://cbonte.github.io/haproxy-dconv/1.7/configuration.html#server

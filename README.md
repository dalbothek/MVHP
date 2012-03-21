# Minecraft VirtualHost Proxy
## Concept
Minecraft 1.2 introduced a new feature which allows Minecraft servers to benefit from the concept of [virtual hosting](http://en.wikipedia.org/wiki/Virtual_hosting). This program serves as a sample implementation of this concept.

## Limitations
* Player's IP addresses are unknown to the actual server, making IP based bans unfeasible.
* The server list query sent by the client (packet 0xfe) doesn't include the hostname, limiting all servers running behind this proxy to display the same server list entry.

## Usage
The proxy runs with Python 2.6+ or PyPy 1.8+

    $ python mvhp.py

### Configuration
The configuration is stored in a file called *config.json* which should be in the working directory when starting the proxy.

Sample configuration:

```
{
  "motd": "Minecraft VirtualHost Proxy",   # MOTD displayed in the server list
  "capacity": 10,                          # Maximal player capacity displayed in the server list
  "players": 3,                            # Connected players displayed in the server list
  "hosts": {                               # Host definitions
    "localhost": {                         # Rule for clients connecting to "localhost"
      "host": "192.168.0.6"                # They are redirected to 192.168.0.6
                                           # The port defaults to 25565 when omited
    },
    "127.0.0.1": {                         # Rule for clients connecting to 127.0.0.1
                                           # The host defaults to "localhost" when omited
      "port": 25566,
      "alias": [                           # This rule also applies to clients connecting 
                                           # to any of the listed aliases
        "127.0.0.2",
        "xyz.dyndns.org"
      ]
    }
  }
}
```

### Reloading the configuration
The configuration can be reloaded without restarting the proxy or disconnecting any clients simply by sending a [SIGHUP](http://en.wikipedia.org/wiki/SIGHUP#Modern_usage) signal to the process.

## License
This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
[http://sam.zoy.org/wtfpl/COPYING](http://sam.zoy.org/wtfpl/COPYING) for more details.

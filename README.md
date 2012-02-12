# Minecraft VirtualHost Proxy
## Concept
The pre-released Minecraft snapshot 12w04a introduced a new feature which allows Minecraft servers to benefit from the concept of [virtual hosting](http://en.wikipedia.org/wiki/Virtual_hosting). This program serves as a sample implementation of this concept.

## Limitations
* Player's IP addresses are unknown to the actual server, making IP based bans unfeasible.
* The server list query sent by the client (packet 0xfe) doesn't include the hostname, limiting all servers running behind this proxy to display the same server list entry.

## License
This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
[http://sam.zoy.org/wtfpl/COPYING](http://sam.zoy.org/wtfpl/COPYING) for more details.


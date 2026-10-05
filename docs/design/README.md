# Design map

One topic, one document. Look the topic up here before writing; extend the document that holds
it.

| Topic | Document | State |
| --- | --- | --- |
| The dependency root, the registry, the doctor, the four module commands, and the move of hub's tree | [Provision](PROVISION.md) | Open: phase B has not started |
| Every module provisioning itself without hub: the selection rule, the `depends_on` closure, the base fragment | [Standalone provisioning](STANDALONE_PROVISIONING.md) | Open: wave 4 of 4 |

The backlog is [Remaining work](REMAINING_WORK.md).

Shipped designs are in the archive. The terminal components, the logo and the help screen are
described in `docs/archive/agent/specs/2026-09-21-terminal-components-design.md`.

The JSON event stream and `--describe` were designed for hub, and their design document is in
the SushiStack repository. What this package implements of them is in
[JSON events](../reference/JSON_EVENTS.md).

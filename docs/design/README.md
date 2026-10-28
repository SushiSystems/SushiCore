# Design map

One topic, one document. Look the topic up here before writing; extend the document that holds
it.

## Topics

<!-- topics:begin -->
| Topic | State | About |
| --- | --- | --- |
| [GPU_TOOLKIT_SELECTION](GPU_TOOLKIT_SELECTION/README.md) | Open | The estate pinned CUDA 12.6.3 on every machine, for one reason: CUDA 13 dropped Pascal (sm_6x), and the owner develops on a Pascal card, so a newer toolkit broke that build at the ptxas... |
| [PROVISION](PROVISION/README.md) | Open | Every Sushi Systems repository must build after one command on any machine. |
| [STANDALONE_PROVISIONING](STANDALONE_PROVISIONING/README.md) | Open | A person who clones one open-source Sushi module must be able to build it after one command, without installing hub. |
<!-- topics:end -->

The backlog is [Remaining work](../backlog/README.md).

Shipped designs are in the archive. The terminal components, the logo and the help screen are
described in the terminal components design spec in the version history.

The JSON event stream and `--describe` were designed for hub, and their design document is in
the SushiStack repository. What this package implements of them is in
[JSON events](../reference/JSON_EVENTS.md).

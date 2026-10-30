# Design map

One topic, one document. Look the topic up here before writing; extend the document that holds
it.

## Topics

<!-- topics:begin -->
| Topic | State | About |
| --- | --- | --- |
| [GPU_TOOLKIT_SELECTION](GPU_TOOLKIT_SELECTION/README.md) | Open | Setup installs the CUDA or ROCm release that this machine's own graphics card supports, instead of one release pinned for every machine. |
| [PROVISION](PROVISION/README.md) | Open | A Sushi module installs its build tools into one dependency root with setup and checks them with doctor, on any machine. |
| [STANDALONE_PROVISIONING](STANDALONE_PROVISIONING/README.md) | Open | A person who clones one Sushi module can set it up and build it with that module's own setup command, without installing the hub. |
<!-- topics:end -->

The backlog is [Remaining work](../backlog/README.md).

Shipped designs are in the archive. The terminal components, the logo and the help screen are
described in the terminal components design spec in the version history.

The JSON event stream and `--describe` were designed for hub, and their design document is in
the SushiStack repository. What this package implements of them is in
[JSON events](../reference/JSON_EVENTS.md).

# Changelog

## Unreleased

- 2026-11-22 — testing: Fixed the slow and failed shard reruns finding no executable when CMake writes a test name in quotes instead of brackets (`source/sushicore/testing/shards.py`, `shard_registrations.py`).

## v0.16.1 — 2026-11-22

- 2026-11-22 — tools: Fixed `rule_unsafe_name` of `check_test_odr.py` flagging rows of a table no instantiation passes, and `std::to_string` of an unsigned member of the parameter (`tools/testing/check_test_odr.py`).

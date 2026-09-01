SHELL := /usr/bin/env bash

.PHONY: link2p-lint link2p-unit link2p-link-sim \
	link2p-host link2p-join link2p-diag-host link2p-diag-join \
	link2p-package link2p-jtbubl-smoke link2p-jtbubl-long \
	link2p-jtbubl-recovery link2p-jtbubl-pause

link2p-lint:
	./scripts/link2p/run-lint.sh

link2p-unit:
	./scripts/link2p/run-unit.sh

link2p-link-sim: link2p-unit

link2p-host:
	./scripts/link2p/build-pocket.sh host

link2p-join:
	./scripts/link2p/build-pocket.sh join

link2p-diag-host:
	./scripts/link2p/build-pocket.sh host diagnostic

link2p-diag-join:
	./scripts/link2p/build-pocket.sh join diagnostic

link2p-package:
	./scripts/link2p/package-link2p.py --rom "$(ROM)" --out "$(OUT)"

link2p-jtbubl-smoke:
	./scripts/link2p/run-jtbubl-determinism.sh smoke "$(ROM)"

link2p-jtbubl-long:
	./scripts/link2p/run-jtbubl-determinism.sh long "$(ROM)"

link2p-jtbubl-recovery:
	./scripts/link2p/run-jtbubl-determinism.sh recovery "$(ROM)"

link2p-jtbubl-pause:
	./scripts/link2p/run-jtbubl-determinism.sh pause "$(ROM)"

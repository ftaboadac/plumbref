# Plumbref Review Harness

This directory runs isolated Codex review passes against Plumbref so the first
feedback pass is repeatable and less anchored.

Run the whole review:

```shell
./reviews/run.sh
```

Run a smaller subset:

```shell
./reviews/run.sh 00-blind-readme 01-technical-trust
```

Outputs are written to `reviews/out/`. Independent reviewer outputs are kept in
a temporary directory until all independent passes complete, then the synthesis
pass reads them together. This keeps the first passes from seeing each other.

## Review Shape

- `00-blind-readme`: what the repo/README communicates without a review packet
- `01-technical-trust`: whether implementation supports the verification claim
- `02-user-value`: whether coding-agent-heavy users would actually run it
- `03-positioning`: whether public language is clear, narrow, and believable
- `04-alternatives`: when existing workflows are good enough
- `05-first-run-friction`: install, setup, first useful result, uninstall risk
- `06-synthesis`: repeated objections, adoption damage, and disproof artifacts

The packet in `reviews/packet/` is deliberately short. Keep it concrete: claims,
demo transcript, failure examples, Plumbref reports, and alternatives.

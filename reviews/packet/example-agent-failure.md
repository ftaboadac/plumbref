# Example Agent Failure Modes

The public-safe validation notes describe two useful failure modes.

## Similar Concepts Blurred

A careful baseline agent got a broad frontend workflow mostly right, but blurred
similar route names and query parameters. Plumbref's value was separating the
older list page gate, newer detail route gate, list-level tab parameter,
drawer-level tab parameter, and a docs/code mismatch.

Why this matters:

- similar-looking code concepts can make a broadly correct answer risky
- engineers may change the wrong parameter or trust a stronger gate than the
  code actually provides

## Wrong Draft Assumption Corrected

A draft claim assumed the codebase used a different feature-flag platform.
Plumbref searched for that assumption, found no support, found evidence for the
actual local flag system, marked the draft claim contradicted, and corrected the
final answer.

Why this matters:

- the report can expose unsupported assumptions and corrections that otherwise
  remain hidden inside an agent's private reasoning

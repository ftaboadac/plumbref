# Public-Safe Validation Story

Date: 2026-06-13

Audience target: README/blog-style example that can become a Show HN section
after the rerun/diff spike proves the next story.

Working headline:

> Plumbref gives coding agents a careful-agent workflow.

Short version:

Plumbref is a local verification harness for coding agents. Instead of relying
on a prompt that asks the agent to be careful, it makes the agent break a repo
answer into claims, search the codebase, read bounded snippets, run
contradiction checks, and leave behind an inspectable report.

The point is not that agents are bad. The point is that risky repo answers
should have a verification trail.

## What We Tested

I ran five paired investigations against a private production monorepo:

- one normal agent run
- one Plumbref-guided run

The baseline was intentionally strong. It was allowed to search broadly, read
source ranges, cite files, and state caveats. This was closer to a careful
senior engineer than to a casual prompt.

The result was not "Plumbref always beats a careful agent." The better result
was more specific:

- five Plumbref answers with no observed unsupported final claims
- one visible self-correction before final answer
- several explicit qualifications where evidence did not support a broader
  claim
- one clear material improvement over the careful baseline
- five inspectable reports showing what was searched, checked, supported, and
  limited

## Example 1: Routing Concepts That Look Similar

One question asked how a frontend workflow gates access and chooses tabs from
the URL.

The careful baseline got the broad flow right, but it blurred several concepts
that share similar route names and query parameters.

Plumbref separated them:

- the older list page gate
- the newer detail route gate
- the list-level tab controlled by one query parameter
- the drawer-level tab controlled by a different query parameter
- a docs/code mismatch where the documentation still used an older route name

That distinction matters. If an engineer changes the wrong query parameter or
assumes the stronger route gate applies to the older list page, they can make a
real change with the wrong mental model.

The value was not a takedown of the baseline. The value was that Plumbref forced
the answer to account for similar-looking concepts before treating the answer as
supported.

## Example 2: A Wrong Draft Assumption Became Visible

Another question asked how feature flags are evaluated and exposed to the
frontend.

During the Plumbref run, a draft claim assumed the codebase used a different
flag platform. Plumbref searched for that assumption, found no support, found
source evidence for the actual local flag system, marked the draft claim
contradicted, and corrected the final answer.

That kind of correction often happens invisibly inside an agent's private
reasoning. In Plumbref, it shows up in the report:

- the unsupported assumption
- the searches that failed to support it
- the source evidence that contradicted it
- the corrected final answer

That is a useful artifact for review. The team does not have to trust that the
agent silently reasoned well; it can inspect the trail.

## What This Supports

This validation supports a narrow, honest claim:

> Plumbref gives you a careful-agent workflow even when you cannot trust that
> the agent will naturally behave like a careful senior engineer.

It does not support these claims:

- Plumbref always beats careful agents.
- Plumbref always saves tokens.
- Plumbref proves code behavior automatically.
- Plumbref replaces human review.

The current value is verified repo answers: source checks, contradiction
checks, explicit qualifications, conservative claim statuses, and a report that
shows what the answer is based on.

## Where This Points Next

The bigger idea is repeatability.

If Plumbref can rerun the same verified claims later, the report becomes more
than a one-off answer. It becomes a way to see when the codebase no longer
supports what the team believed.

Future story:

> Your team's verified claims about how the codebase works, updated when the
> code changes.

That is the rerun/diff demo to build next.

## Screenshot Brief

Primary screenshot candidate for the current report-style demo:

- Use the routing example.
- Show the question at the top.
- Show a compact list of claim statuses.
- Highlight the claim where Plumbref separated the list tab from the drawer
  tab.
- Show two or three source evidence rows, with private paths abstracted.
- Show a short final answer that uses careful wording.
- Include a visible "limits" or "qualification" section.

What the screenshot should communicate in five seconds:

> This is the artifact I want before changing a risky flow.

Avoid:

- a comparison chart as the primary visual
- "agent was wrong" framing
- token-savings as the main message
- private repo paths or private domain terms

Secondary screenshot candidate:

- Use the feature-flag example.
- Show one contradicted draft claim.
- Show the final answer corrected by checked evidence.
- Use it to explain why visible self-correction matters.

This is a stronger supporting example than a primary screenshot because it is
about correctness. The routing example is better for first impression because
it shows the practical shape of a careful repo answer.

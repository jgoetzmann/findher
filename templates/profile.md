# Profile

Every block carries a source. `profile.py` parses this table to build its own
refusal list, so the guard cannot drift from the spec.

Sources that are postable: `likeness:<line>`, `interview:<key>`, `observed`,
`seed-neutral`. Sources that are not: `invented`, `aspirational`, `unfillable`.
A block sourced to one of those three prints as a blank with its question still
attached, and a blank you cannot fill is a wrong question, not a hard question.

## Blocks

| block | max | source | text |
|---|---|---|---|
| headline | 60 | unfillable |  |
| about | 300 | unfillable |  |
| prompt_1 | 140 | unfillable |  |
| prompt_2 | 140 | unfillable |  |

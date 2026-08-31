# The likeness prompt

Hand this to the user verbatim. Nothing in the plan may claim anything about
them that is not sourced to the output of this, or to something they typed into
the interview.

> Paste this into ChatGPT, Claude, or whichever assistant you have the longest
> history with. Run it in a **new chat** so it draws on your history rather than
> the current thread. Run it in more than one assistant if you have more than
> one — they surface different things, and the disagreements are informative.

```
Write me a "likeness handoff" — a document that would let another person, or another
model, understand and represent me accurately.

Base it ONLY on what has actually appeared in our conversations. This is the most
important instruction in this prompt: I am going to use this document as a source of
truth, and anything you invent will end up somewhere I have to defend it out loud.

Sort every single statement into one of four labels, and put the label on it:

  OBSERVED  — I said this, or it is directly visible in something I wrote.
              Quote me where you can, including my typos and my actual phrasing.
  INFERRED  — you are reasonably confident but I never said it. Say what it is
              inferred from.
  UNCERTAIN — you have a weak signal and you are guessing.
  UNKNOWN   — you have nothing. List these explicitly at the end. A named gap is
              useful to me; a confident guess is worse than useless.

Rules:

1. Do NOT invent my physical appearance. If I have never described how I look, the
   correct output is "appearance: UNKNOWN", not a description. Same for my age,
   ethnicity, health, religion, politics, and anything else I have not stated.
2. Do NOT smooth out my voice. Keep my slang, my sentence rhythm, my typos, and the
   words I overuse. If I use a word in a non-standard way, say so and say what I
   seem to mean by it, because that is exactly the kind of thing that gets
   misread. If a word I used has two possible readings, give both and say you are
   not sure which I meant.
3. Refer to other people by initial and relationship — "A., a friend from home" —
   never by full name, and never by anything medical or private about them. They did
   not agree to be in this document.
4. Prefer specifics over summary. "He signed up for an intensive language course
   within two days of deciding to" is useful. "He is impulsive" is not.

Cover: how I think and talk; what I actually do with my time, with evidence; things
I have finished and things I abandoned; running jokes and bits; how I handle being
wrong; what I am good at, with the receipts; what I avoid; and anything about me
that a stranger would find genuinely unusual.

Then end with two sections:
  GAPS   — everything you had to mark UNKNOWN.
  RISKS  — anything in here you think I would dispute, or that you are least
           confident about.
```

## What to do with the output

Save it into the plan repo as `likeness-<source>.md`. It is gitignored on
arrival — it is the most sensitive file in the repo, and the exposure in it is
mostly other people's. Then every claim in the generated profile gets a row in a
provenance table citing it.

**If the user will not or cannot run it**, the skill does not get to guess. It
writes a blank with the question still next to it.

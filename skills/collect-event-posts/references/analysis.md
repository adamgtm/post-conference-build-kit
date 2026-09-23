# Analyze the posts and choose an angle

Read templates/business-brief.md as filled by the reader. If company context is missing, get it before proposing a company-specific angle.

## Establish the dataset

Work from confirmed posts.csv. Count rows, unique captured author identities, and reactions/comments/reposts in code. If author identity is missing, report known identities rather than treating names as unique people. Keep reshares distinguishable from original posts. Record the snapshot date.

Read the most engaged posts, a reproducible random selection of quieter posts, and examples across dates and author types. For a large dataset, save labeled batches and read the full text behind every proposed claim. A model-generated summary is a navigation aid.

Look for questions, disagreements, repeated problems, proof, product claims, and a gap between language and demonstrated work. For each theme record the relevant post URLs, unique known authors, and representative examples. Distinguish post share, author share and engagement share. Do not infer agreement from a reaction.

Classify affiliation from evidence when necessary. Someone who works on Salesforce projects is not thereby a Salesforce employee. Leave uncertainty visible.

## Propose three angles

For each, supply:

- The intended reader and specific problem.
- A hook and point of view.
- Supporting source posts and the strongest counterexample.
- What the company can credibly contribute.
- A useful offer and next action.
- What evidence would weaken the recommendation.

Rank by relevance to the reader, strength of evidence, company fit, and a useful contribution. Explain your judgment. Do not manufacture precision with a numeric “angle score.”

Distinguish findings from hypotheses about campaign performance. “Few collected posts describe a build” cannot establish that few people build in private. Look at the underlying posts before turning a chart label into a claim about people.

## Worked decision

Adam's campaign connects a conversation about AI building to a first build a marketer can try. The offer provides the collection method, source material and starting instructions. The angle becomes useful because the reader can do something with it.

For a different company, the same dataset might support a different choice: explain a customer implementation, publish a narrowly useful workflow, or answer a repeated question with evidence. A generic event recap is only one possible output.

Write output/angles.md and fill templates/campaign-worksheet.md as output/campaign-strategy.md. Do not describe planned ads, matching or acquisition results as completed.

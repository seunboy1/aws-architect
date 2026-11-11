# Layout rules

These came from diagrams that looked wrong and were fixed. The linter enforces the starred ones.

1. **One flow direction.** Left to right (or top to bottom) for the main path. Branches and return paths may go the other way but never fight the main flow.
2. **Group by trust boundary.** Account, then VPC, then public and private subnets. Services AWS runs for you (S3, DynamoDB, SQS, SNS, Bedrock, Secrets Manager, API Gateway, CloudFront) sit **outside** the VPC; if a workload in the VPC reaches them privately, show a **VPC endpoint** icon inside. Do not draw a managed service inside a subnet, because that claims it sits behind the subnet's security rules.
3. **Cross-cutting concerns as a band.** IAM, KMS, CloudTrail, Config, CloudWatch, Budgets go in one dashed zone labelled "applies to everything" with no arrows, unless a specific attachment matters.
4. **Labels on the free side.** Icon text defaults to the bottom. If an arrow leaves or enters through the bottom, put that icon's label on `top` or `left`. *
5. **No line through anything.** Connectors must not cross another icon or its label. Route round it with `via` points. *
6. **Orthogonal lines only.** Every segment horizontal or vertical; give explicit `exit`, `entry` and `via`. Diagonal or unspecified routes make draw.io guess. *
7. **Crossings.** Avoid them. If unavoidable, set `hop: true` on the less important line.
8. **Dashed means not the main path:** asynchronous, return, redrive, optional.
9. **Edge labels are 1-3 words** ("webhook", "queued message", "writes PDF"). If a label needs a sentence, put it in the footnote.
10. **No overlaps; stay inside the parent.** *
11. **Budget.** About 14 icons and 12 arrows per diagram. Past that, split into overview plus detail.
12. **Title top-left; footnote and notes outside the account frame** at the bottom. No legend floating inside the diagram.
13. **Do not invent.** Draw only what the user confirmed. Mark guesses in the footnote and in your hand-off message.
14. **Availability Zones.** An icon has one parent group. To show two AZs, nest two `zone` groups ("Availability Zone A" and "B") inside the VPC with a subnet group inside each, and draw a workload once per AZ if it really runs in both. If it is simpler, draw it once inside a group labelled "Private subnets (2 AZs)" and say so.
15. **Where outside things go.** Users and clients on the left, outside the account frame. CI/CD tools and third-party services also sit outside the frame, on the side their arrows leave from. Registries such as ECR and artifact stores go in the managed-services zone, not in a subnet.
16. **Several lines turning near each other.** Stagger their turn positions by about 12 px and check the preview for crossings; if a pair crosses, swap their turn positions. Keep lines out of group titles (top-left of each group); the linter warns about that.
17. **Look at it.** Rendering and inspecting at 1:1 is part of the job (SKILL.md step 5).

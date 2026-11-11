# Cost estimate: calculator.aws link

## How it works

calculator.aws has no public API. Its own Share button posts the whole estimate as JSON to
`https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs` and gets back an id; the public link is
`https://calculator.aws/#/estimate?id=<id>`. `scripts/calculator_link.py` builds that JSON from
the calculator's published service definitions (`d1qsjq9pzbk1k6.cloudfront.net/data/<serviceCode>/en_US.json`)
and posts it. The endpoint is undocumented; if posting starts failing, capture a fresh Share
request in the browser (network tab, `saveAs`) and compare its body with `--dry-run` output.

**A posted link opens read-only with the costs stored in it.** The script stores $0, so the
link must be priced once in a browser: open it, reload, click *Update estimate*, wait for every
row to say "Cost updated" (a $0 free-tier row may stay "-"), then *Share* > *Agree and continue*
and copy the new link from the dialog's text field. The AWS sales chat bubble covers the Agree
button; remove `#chatbot-wrapper` first. Open the final link once more to confirm the totals.

## usage.json

```json
{
 "name": "Customer - project (indicative, eu-west-1)",
 "region": "eu-west-1",
 "services": [
  {"service": "aWSLambda", "description": "API functions",
   "fields": {"numberOfRequests": [5000000, "perMonth"], "durationOfEachRequest": 300,
              "sizeOfMemoryAllocated": [512, "mb"]}},
  {"service": "amazonCloudFront", "template": "CDN", "description": "Static site",
   "fields": {"dataTransferedToInternet_EU": [500, "gb"]}}
 ]
}
```

- `service`: the calculator's service code. Sub-services such as `amazonS3Standard`,
  `dynamoDbOnDemand` and `rekognitionImage` are wrapped in their parent automatically.
- `template`: only when a service has several (CloudFront's first is the flat-rate plan; use `CDN`
  for pay-as-you-go). `--fields <code>` lists them.
- `fields`: `id: value` or `id: [value, unit]`. Units: frequency fields take the option id
  (`perMonth`); size fields take `gb`, `tb`, `mb` or `kb`; the script appends the period.
  Fields you leave out get the website's defaults (dropdown first option, prefilled numbers).
- `region` per service overrides the top-level one. Check the service exists there:
  `curl -s https://d1qsjq9pzbk1k6.cloudfront.net/manifest/regionList/publish.json` maps each
  service code to its regions (Local Zones appear as codes such as `af-south-1-los-1`).

## Sizing by customer stage

Ask for real numbers first (users, uploads, requests, GB). When the customer does not know, start
from the stage they gave in the kickoff, say which you used, and mark the estimate "indicative".

| stage | typical month | example |
|---|---|---|
| Startup or MVP | hundreds to low thousands of active users, tens of thousands of API requests, 10-100 GB stored, one Region, no multi-AZ databases or NAT per AZ unless asked | event photo face search (`assets/example-usage.json`): about $33/month |
| Growing product | tens of thousands of users, millions of requests, 0.5-5 TB, multi-AZ for stateful tiers | |
| Enterprise | price from their own figures; do not guess | |

For a startup, keep always-on items (NAT gateways, provisioned databases, load balancers) out
unless the design needs them; they dominate a small bill. Do not apply the free tier or credits in
the calculator; mention them in the hand-off instead (AWS Free Tier, and AWS Activate credits for
startups).

## Unit traps (read the dry-run lines)

- SQS requests are in **millions** (`1` = 1M requests). Some Lambda, DynamoDB and CloudFront
  fields offer `millionPerMonth` too; the dry-run line shows which one you chose.
- API Gateway multiplies requests by `RESTMult` / `APIOpsMult` (defaults: millions for HTTP,
  set `"RESTMult": "1"` for an exact REST count).
- S3 storage is `[GB, "gb"]` per month; DynamoDB storage is total GB.

## Field ids checked in a priced estimate (2026-11-08)

| service code | fields used |
|---|---|
| `rekognitionImage` | `indexFacesAPI`, `searchFacesbyImageAPI`, `facesStored` |
| `amazonS3Standard` | `s3StandardStorageSize`, `s3StandardPutRequests`, `s3StandardGetRequests` |
| `aWSLambda` | `numberOfRequests`, `durationOfEachRequest`, `sizeOfMemoryAllocated` |
| `dynamoDbOnDemand` | `dataStorageSize`, `writeRateId`, `readRateId` |
| `amazonSimpleQueueService` | `standardQueueRequests` (millions) |
| `amazonApiGateway` | `RESTMult`, `numberOfRESTRequests` |
| `amazonCloudFront` (template `CDN`) | `dataTransferedToInternet_<EU/US/SA/...>`, `numberOfHttpsRequests_<...>` |
| `awsKeyManagementService` | `numberOfCmk`, `numberOfSymmetricRequests` |
| `amazonCloudWatch` | `sizeOfStandardLogsDataIngested`, `numberOfStandardAlarms`, `numberOfDashboards` |

Other services work the same way but were not yet checked against a priced estimate; check
their lines by hand the first time. `assets/example-usage.json` is a full example.

## Known oddity

Rekognition Image: the calculator showed $490 for 240k Group 1 calls plus 1M stored faces in
eu-west-1, while its own price table gives $0.001 per image and $0.00001 per face-month (about
$250). Same result when the form is filled by hand, so it is the calculator, not the script.
Tell the user rather than adjusting the numbers.

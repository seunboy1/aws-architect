# Icon names

Every name below was checked by rendering it in draw.io's viewer: it shows a real AWS glyph. Use these exact strings as `icon` in the spec. A name with `*` is a **direct shape** (outlined glyph, no gradient square); the script already knows which are which.

If you need a service that is not listed: add its likely draw.io name to `CANDIDATES` in `scripts/icon_sheet.py`, run it, preview the result, and only add names that show a real glyph (a plain coloured square means the name is wrong). Then add the verified names to `build_drawio.py` with `_add(...)` and to this file.

**Known blank (wrong name, do not use):** `s3_glacier`, `opensearch_service` (use `elasticsearch_service`), `systems_manager_parameter_store`, `iam_identity_center`, `appconfig`, `ec2_auto_scaling` (use `auto_scaling2`), `sagemaker_ai` (use `sagemaker`). For a service with no working icon, use a `box` node.

Category colours are chosen automatically from the icon (compute orange, integration pink, database blue, storage green, security red, networking purple, management magenta, AI teal, dev tools blue).

## Compute and containers

`amplify`, `app_runner`, `auto_scaling2`, `batch`, `ec2`, `ecr`, `ecs`, `eks`, `elastic_beanstalk`, `fargate`, `iot_core`, `lambda`, `lightsail`

## Integration and messaging

`api_gateway`, `appflow`, `appsync`, `eventbridge`, `kinesis`, `kinesis_data_analytics`, `kinesis_data_firehose`, `kinesis_video_streams`, `managed_streaming_for_kafka`, `managed_workflows_for_apache_airflow`, `mq`, `simple_email_service`, `sns`, `sqs`, `step_functions`

## Networking

`app_mesh`, `application_load_balancer*`, `cloud_map`, `cloudfront`, `customer_gateway*`, `direct_connect`, `elastic_load_balancing`, `endpoints*`, `global_accelerator`, `internet_gateway*`, `nat_gateway*`, `network_load_balancer*`, `privatelink`, `route_53`, `router*`, `site_to_site_vpn*`, `transit_gateway`, `virtual_private_cloud`, `vpn_gateway*`

## Databases and analytics

`athena`, `aurora`, `data_exchange`, `database_migration_service`, `documentdb_with_mongodb_compatibility`, `dynamodb`, `elasticache`, `elasticsearch_service`, `emr`, `glue`, `glue_databrew`, `keyspaces`, `lake_formation`, `memorydb_for_redis`, `neptune`, `quicksight`, `rds`, `redshift`, `timestream`

## Storage

`backup`, `datasync`, `elastic_block_store`, `elastic_file_system`, `fsx`, `s3`, `snowball`, `storage_gateway`, `transfer_family`

## AI and ML

`bedrock`, `bedrock_agentcore`, `comprehend`, `kendra`, `lex`, `polly`, `rekognition`, `sagemaker`, `textract`, `transcribe`

## Management and governance

`budgets`, `cloudformation`, `cloudtrail`, `cloudwatch`, `cloudwatch_2`, `config`, `control_tower`, `organizations`, `systems_manager`, `trusted_advisor`, `xray`

## Security

`certificate_manager`, `cognito`, `detective`, `directory_service`, `firewall_manager`, `guardduty`, `identity_and_access_management`, `inspector`, `key_management_service`, `macie`, `network_firewall`, `secrets_manager`, `security_hub`, `security_lake`, `shield`, `verified_access`, `waf`

## Users and clients

`client*`, `corporate_data_center*`, `internet*`, `mobile_client*`, `traditional_server*`, `user*`, `users*`

## Developer tools

`codeartifact`, `codebuild`, `codecommit`, `codedeploy`, `codepipeline`

## Choosing between similar icons

- `ecs` is the container orchestrator (cluster or service); `fargate` is the serverless compute that runs the tasks. For "ECS service on Fargate" use `fargate` and say "ECS service" in the sub-label, or use both if the distinction matters.
- `rds` is a generic relational database; use `aurora` only when the engine is Aurora.
- `users` is a crowd of end users, `user` one person, `client` a laptop or browser, `mobile_client` a phone, `internet` the public internet, `corporate_data_center` and `traditional_server` on-premises systems.
- `cloudwatch` and `cloudwatch_2` both render; use `cloudwatch_2`.
- `endpoints` is a VPC endpoint (interface or gateway); say which in the sub-label.
- No icon for a third-party service (Twilio, Stripe, GitHub): use a `box` node.

#!/usr/bin/env python3
"""Maintainer tool: draw a sheet of CANDIDATE icon names so you can see which render.

Usage: python icon_sheet.py out.drawio  (edit CANDIDATES to the new names first), then preview it. Names that show a real glyph can be added to
ICONS in build_drawio.py (verified=True) and references/icons.md. A plain coloured square means the
shape name is wrong (or needs the other style: set direct=True/False below).
"""
import sys

import build_drawio as b

# name:category:direct  (direct = shape=mxgraph.aws4.<name> instead of a resourceIcon)
# Already verified and now in build_drawio.ICONS; kept as a worked list. Known blank (wrong name): s3_glacier, opensearch_service.
CANDIDATES = """
ec2:compute ecs:compute eks:compute batch:compute elastic_beanstalk:compute lightsail:compute app_runner:compute ecr:compute
elastic_file_system:storage elastic_block_store:storage backup:storage s3_glacier:storage
rds:db elasticache:db redshift:db neptune:db documentdb_with_mongodb_compatibility:db memorydb_for_redis:db keyspaces:db timestream:db
cloudfront:net route_53:net transit_gateway:net direct_connect:net global_accelerator:net privatelink:net virtual_private_cloud:net
network_load_balancer:net:d internet_gateway:net:d vpn_gateway:net:d site_to_site_vpn:net:d customer_gateway:net:d router:net:d
sns:integ eventbridge:integ step_functions:integ appsync:integ mq:integ kinesis:integ kinesis_data_firehose:integ appflow:integ
cognito:security shield:security guardduty:security security_hub:security inspector:security certificate_manager:security
detective:security macie:security firewall_manager:security network_firewall:security
systems_manager:mgmt cloudformation:mgmt organizations:mgmt control_tower:mgmt xray:mgmt trusted_advisor:mgmt cloudwatch:mgmt
codebuild:dev codepipeline:dev codecommit:dev codedeploy:dev
sagemaker:ai textract:ai rekognition:ai comprehend:ai lex:ai polly:ai transcribe:ai kendra:ai
athena:db glue:db emr:db opensearch_service:db quicksight:db lake_formation:db
amplify:compute simple_email_service:integ
users:user:d mobile_client:user:d client:user:d internet:user:d corporate_data_center:user:d traditional_server:user:d
""".split()


COLS = 4


def main(out):
    nodes = []
    for i, tok in enumerate(CANDIDATES):
        name, cat, *rest = tok.split(":")
        b.ICONS[name] = (cat, bool(rest), False)
        nodes.append({"id": f"n{i}", "label": name[:26], "icon": name, "cx": 110 + (i % COLS) * 220, "top": 60 + (i // COLS) * 130})
    spec = {"title": "Icon candidates", "canvas": {"width": 110 + COLS * 220, "height": 60 + (len(nodes) // COLS + 1) * 130 + 60},
            "groups": [], "nodes": nodes, "edges": []}
    open(out, "w", encoding="utf-8").write(b.build(b.depth_sort(spec)))
    print("wrote", out, len(nodes), "icons")


if __name__ == "__main__":
    main(sys.argv[1])

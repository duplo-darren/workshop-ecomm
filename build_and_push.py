"""Build and push Docker images for each microservice to ECR.

Creates the ECR repository for each service if it does not already exist, then
builds and pushes the image.

Usage:
    python build_and_push.py                    # prompts for prefix and tag
    python build_and_push.py <prefix> <tag>     # non-interactive
    ECR_REPO_PREFIX=ecomm IMAGE_TAG=v1.1.0 python build_and_push.py
"""

import base64
import json
import os
import subprocess
import sys

import boto3

SERVICES = ["catalog", "inventory", "frontend"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_account_id():
    sts = boto3.client("sts")
    return sts.get_caller_identity()["Account"]


def ecr_login(region, registry):
    ecr = boto3.client("ecr", region_name=region)
    token_response = ecr.get_authorization_token()
    auth = token_response["authorizationData"][0]
    token = base64.b64decode(auth["authorizationToken"]).decode()
    username, password = token.split(":", 1)
    subprocess.run(
        ["docker", "login", "--username", username, "--password-stdin", registry],
        input=password.encode(),
        check=True,
    )


def ensure_repository(region, repo):
    """Create the ECR repository if it is not already there."""
    ecr = boto3.client("ecr", region_name=region)
    try:
        ecr.create_repository(
            repositoryName=repo,
            imageScanningConfiguration={"scanOnPush": True},
        )
        print(f"Created ECR repository {repo}")
    except ecr.exceptions.RepositoryAlreadyExistsException:
        print(f"ECR repository {repo} already exists")


def build_and_push(service, region, registry, repo_prefix, tag):
    build_context = os.path.join(SCRIPT_DIR, "microservices", service)
    repo = f"{repo_prefix}-{service}"
    image_tag = f"{registry}/{repo}:{tag}"

    print(f"\n--- {service} ---")
    ensure_repository(region, repo)

    print(f"Building {image_tag} ...")
    subprocess.run(
        ["docker", "build", "-t", image_tag, build_context],
        check=True,
    )

    print(f"Pushing {image_tag} ...")
    subprocess.run(["docker", "push", image_tag], check=True)
    print(f"Done: {image_tag}")


def resolve(name, cli_value, env_var, prompt):
    value = cli_value or os.environ.get(env_var) or input(prompt).strip()
    if not value:
        print(f"No {name} provided, aborting.")
        sys.exit(1)
    return value


def main():
    args = sys.argv[1:]
    repo_prefix = resolve(
        "prefix", args[0] if len(args) > 0 else None,
        "ECR_REPO_PREFIX", "Please enter your prefix: ",
    )
    tag = resolve(
        "tag", args[1] if len(args) > 1 else None,
        "IMAGE_TAG", "Image tag (e.g. v1.0.0): ",
    )

    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

    print("Retrieving AWS account ID via STS...")
    account_id = get_account_id()
    registry = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
    print(f"Registry: {registry}")

    print("Logging in to ECR...")
    ecr_login(region, registry)

    for service in SERVICES:
        build_and_push(service, region, registry, repo_prefix, tag)

    print("\nAll images pushed successfully.")
    print("\nDeploy with:")
    print(
        f"  helm upgrade --install ecomm helm/ecomm \\\n"
        f"    --set image.registry={registry} \\\n"
        f"    --set image.repositoryPrefix={repo_prefix} \\\n"
        f"    --set image.tag={tag}"
    )


if __name__ == "__main__":
    main()

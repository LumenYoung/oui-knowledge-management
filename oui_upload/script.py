import requests
import os
import glob
from argparse import ArgumentParser


def find_knowledge_by_name(base_url, token, kb_name):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Get knowledge list
    response = requests.get(f"{base_url}/api/v1/knowledge/list", headers=headers)
    if not response.ok:
        raise Exception(f"Failed to get knowledge list: {response.text}")

    # Find matching knowledge base
    for kb in response.json():
        if kb["name"] == kb_name:
            return kb

    raise ValueError(f"Knowledge base '{kb_name}' not found")


def sync_files_to_knowledge(base_url, token, kb_name):
    # 1. Find knowledge base
    try:
        kb = find_knowledge_by_name(base_url, token, kb_name)
    except Exception as e:
        print(str(e))
        return

    kb_id = kb["id"]
    print(f"Found knowledge base '{kb_name}' with ID: {kb_id}")

    # 2. Get existing files
    existing_files = {f["meta"]["name"] for f in kb.get("files", [])}
    print(f"Found {len(existing_files)} existing files in knowledge base")

    # 3. Process files in current directory
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    file_types = [
        "*.txt",
        "*.md",
        "*.py",
        "*.js",
        "*.html",
        "*.css",
        "*.json",
        "*.yaml",
        "*.yml",
        "*.sh",
        "*.bat",
        "Dockerfile",
        "LICENSE",
    ]

    files_uploaded = 0
    current_dir = os.getcwd()

    for pattern in file_types:
        for file_path in glob.glob(
            os.path.join(current_dir, "**", pattern), recursive=True
        ):
            # Skip .git directories
            if ".git" in file_path:
                continue

            file_name = os.path.basename(file_path)

            if file_name not in existing_files:
                try:
                    # Upload file
                    with open(file_path, "rb") as f:
                        upload_response = requests.post(
                            f"{base_url}/api/v1/files/",
                            headers=headers,
                            files={"file": f},
                        )

                    if not upload_response.ok:
                        print(f"Failed to upload {file_name}: {upload_response.text}")
                        continue

                    file_id = upload_response.json().get("id")

                    # Add to knowledge base
                    add_response = requests.post(
                        f"{base_url}/api/v1/knowledge/{kb_id}/file/add",
                        headers=headers,
                        json={"file_id": file_id},
                    )

                    if add_response.ok:
                        files_uploaded += 1
                        print(f"Added {file_name} to knowledge base")
                    else:
                        print(f"Failed to add {file_name}: {add_response.text}")

                except Exception as e:
                    print(f"Error processing {file_name}: {str(e)}")

    print(
        f"\nSync complete! Uploaded {files_uploaded} new files to knowledge base '{kb_name}'"
    )


if __name__ == "__main__":
    parser = ArgumentParser(description="Sync files to a knowledge base")
    parser.add_argument("--token", "-t", required=True, help="OpenWebUI API token")
    parser.add_argument(
        "--base-url",
        "-u",
        required=True,
        help="OpenWebUI base URL (e.g., http://localhost:3000)",
    )
    parser.add_argument(
        "--kb-name", "-n", required=True, help="Name of the knowledge base to sync with"
    )

    args = parser.parse_args()

    sync_files_to_knowledge(
        base_url=args.base_url, token=args.token, kb_name=args.kb_name
    )

import requests
import os
import glob
import hashlib
from argparse import ArgumentParser


def find_knowledge_by_name(base_url, token, kb_name):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Get knowledge list (API changed; use /knowledge/ and read "items")
    response = requests.get(f"{base_url}/api/v1/knowledge/", headers=headers)
    if not response.ok:
        raise Exception(f"Failed to get knowledge list: {response.text}")

    payload = response.json()
    items = payload.get("items", payload if isinstance(payload, list) else [])

    # Find matching knowledge base
    for kb in items:
        if kb.get("name") == kb_name:
            return kb

    raise ValueError(f"Knowledge base '{kb_name}' not found")


def sync_files_to_knowledge(base_url, token, kb_name, target_dir=None):
    # 1. Find knowledge base
    try:
        kb = find_knowledge_by_name(base_url, token, kb_name)
    except Exception as e:
        print(str(e))
        return

    kb_id = kb["id"]
    print(f"Found knowledge base '{kb_name}' with ID: {kb_id}")

    # 2. Get existing files (API now exposes files via /knowledge/{id}/files)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    existing_hashes = set()
    existing_names = set()
    page = 1
    total = None
    while True:
        files_response = requests.get(
            f"{base_url}/api/v1/knowledge/{kb_id}/files",
            headers=headers,
            params={"page": page},
        )
        if not files_response.ok:
            print(
                f"Warning: Failed to get existing files list: {files_response.text}"
            )
            break

        payload = files_response.json()
        items = payload.get("items", [])
        if total is None:
            total = payload.get("total")

        for item in items:
            if item.get("hash"):
                existing_hashes.add(item["hash"])
            if item.get("filename"):
                existing_names.add(item["filename"])

        if not items:
            break

        if total is not None and len(existing_names) >= total:
            break

        page += 1

    print(f"Found {len(existing_names)} existing files in knowledge base")

    # 3. Process files in current directory

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
    # Determine the directory to search in
    if target_dir is None:
        search_dir = os.getcwd()
    else:
        search_dir = target_dir
    
    # Convert to absolute path
    search_dir = os.path.abspath(search_dir)
    print(f"Searching for files in: {search_dir}")

    for pattern in file_types:
        # Search recursively in the specified directory
        for file_path in glob.glob(
            os.path.join(search_dir, "**", pattern), recursive=True
        ):
            # Skip .git directories
            if ".git" in file_path:
                continue

            file_name = os.path.basename(file_path)

            if file_name not in existing_names:
                try:
                    # Get file info for debugging
                    file_size = os.path.getsize(file_path)
                    print(f"Processing file: {file_path} (size: {file_size} bytes)")
                    
                    if file_size == 0:
                        print(f"Warning: File is empty: {file_path}")
                        continue

                    # Compute hash for dedup
                    sha256 = hashlib.sha256()
                    with open(file_path, "rb") as hf:
                        for chunk in iter(lambda: hf.read(1024 * 1024), b""):
                            sha256.update(chunk)
                    file_hash = sha256.hexdigest()

                    if file_hash in existing_hashes:
                        print(f"Skipping duplicate content: {file_name}")
                        continue
                    if file_name in existing_names:
                        print(f"Skipping existing filename: {file_name}")
                        continue

                    # Upload file
                    with open(file_path, "rb") as f:
                        upload_response = requests.post(
                            f"{base_url}/api/v1/files/",
                            headers=headers,
                            files={"file": (file_name, f, "application/octet-stream")},
                        )

                    if not upload_response.ok:
                        print(f"Failed to upload {file_name}: {upload_response.text}")
                        continue

                    file_id = upload_response.json().get("id")
                    print(f"File uploaded successfully, ID: {file_id}")

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
                        if "Duplicate content detected" in add_response.text:
                            print(f"Duplicate content detected for {file_name}; skipping")
                            existing_hashes.add(file_hash)
                            continue
                        print(f"Failed to add {file_name} to knowledge base: {add_response.text}")

                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

    print(
        f"\nSync complete! Uploaded {files_uploaded} new files to knowledge base '{kb_name}'"
    )


def main():
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
    parser.add_argument(
        "--dir", "-d", help="Target directory to upload (defaults to current directory)"
    )

    args = parser.parse_args()

    sync_files_to_knowledge(
        base_url=args.base_url,
        token=args.token,
        kb_name=args.kb_name,
        target_dir=args.dir
    )

if __name__ == "__main__":
    main()

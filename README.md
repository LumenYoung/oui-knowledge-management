# oui-upload

A command-line tool to sync local files with an OpenWebUI knowledge base.

## Installation

```bash
pip install oui-upload
```

## Usage

```bash
oui-upload --token YOUR_API_TOKEN --base-url http://your-openwebui-instance:3000 --kb-name "Your Knowledge Base"
```

### Arguments

- `--token`, `-t`: Your OpenWebUI API token (required)
- `--base-url`, `-u`: Base URL of your OpenWebUI instance (required)
- `--kb-name`, `-n`: Name of the knowledge base to sync with (required)

## Supported File Types

The tool will automatically scan and upload files with the following extensions:
- .txt
- .md
- .py
- .js
- .html
- .css
- .json
- .yaml, .yml
- .sh
- .bat
- Dockerfile
- LICENSE

Files in `.git` directories are automatically excluded.

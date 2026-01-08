# AI Game Referee - Rock-Paper-Scissors-Plus (ADK Edition)

This project uses the **Google Agent Development Kit (ADK)**.

## Setup

1.  **Install ADK**:
    ```bash
    pip install google-adk
    ```

2.  **Configuration**:
    - Ensure `.env` has your `GOOGLE_CLOUD_PROJECT` set.
    - Run `gcloud auth application-default login`.

3.  **Run the Agent**:
    ```bash
    adk run
    ```
    (Or `python agent.py` if testing basic logic without the full runner)


## Prerequisites

1.  **Google Cloud SDK (Required for `gcloud`)**
    - **Download & Install**: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
    - After installing, verify by running `gcloud --version` in a new terminal.
    - **Initial Setup**: Run `gcloud init` to set up your configuration.

2.  **Google Cloud Project**
    - Enable **Vertex AI API** in your project console.
    - **Enable Billing**: The project must have a billing account linked to use Vertex AI.

3.  **Python Dependencies**
    ```bash
    pip install google-adk google-cloud-aiplatform
    ```

## Authentication Setup

### Option 1: Gcloud CLI (Recommended)
1.  Run `gcloud auth application-default login`.
2.  Login via browser.

### Option 2: Service Account Key (Alternative)
If you cannot install `gcloud`:
1.  Go to [Google Cloud Console > IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
2.  Create a Service Account.
3.  Create a new **Key** (JSON format) and download it.
4.  Save the file as `credentials.json` in this folder.
5.  Set the environment variable in your terminal (or add to `.env` if using a loader that supports it, though usually manual export is safer):
    ```bash
    # Windows PowerShell
    $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\credentials.json"
    
    # Linux/Mac
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
    ```

## Running the Game

You need to provide your Google Cloud Project ID. You can do this in two ways:

### Option 1: Environment Variable (Recommended)

Set the `GOOGLE_CLOUD_PROJECT` environment variable before running the script.

**Windows (PowerShell):**
```powershell
$env:GOOGLE_CLOUD_PROJECT="your-project-id-here"
python game_referee.py
```

**Linux/Mac:**
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id-here"
python game_referee.py
```

### Option 2: Interactive Input
If the environment variable is not set, the script will ask you to enter your Project ID when it starts.

```bash
python game_referee.py
```

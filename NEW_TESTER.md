# OpenAI Multi-Profile Key Scanner

The Multi-Profile Scanner is designed to categorize your API keys based on their specific capabilities. Instead of testing one model at a time, you can now define a configuration file that tells the script exactly what "tiers" of keys you are looking for.

## 🚀 Key Features

* **Metadata First:** Fetches the full list of available models for each key without spending credits.
* **Live Activity Verification:** Performs a 1-token completion on a "Primary Model" to ensure the key has an active billing status/quota.
* **Extra Capability Mapping:** Checks if high-value models (DALL-E 3, Whisper, etc.) are enabled on the account via metadata.
* **JSON Config Driven:** Define multiple test profiles (e.g., a "GPT-4o Tier" and an "o1 Tier") and run them all at once.
* **Dual Output:** Generates a human-readable summary and a detailed JSON report.

---

## 🛠 Configuration (`config.json`)

Define your testing profiles in a `config.json` file. Each profile consists of:

1. `primary_model`: The model used for the **Live Completion** (ensures key is active).
2. `extras`: A list of models to look for in the metadata (checked without calling them).

**Example `config.json`:**

```json
[
  {
    "primary_model": "gpt-4o",
    "extras": ["dall-e-3", "whisper-1", "gpt-4-turbo"]
  },
  {
    "primary_model": "gpt-4o-mini",
    "extras": ["gpt-3.5-turbo"]
  },
  {
    "primary_model": "o1-preview",
    "extras": ["dall-e-3"]
  }
]

```

---

## 📖 Usage

### 1. Prepare your files

Ensure you have a `keys.txt` (one key per line) and your `config.json` in the script directory.

### 2. Run the scanner

```bash
python new_tester.py --file results/github_keys_sharded_20260311-233117_keys.txt --config config.json --workers 20

```

### 3. Command Line Arguments

| Argument | Short | Default | Description |
| --- | --- | --- | --- |
| `--file` | `-f` | `keys.txt` | Path to the file containing API keys. |
| `--config` | `-c` | `config.json` | Path to the JSON profile configuration. |
| `--workers` | `-w` | `10` | Number of parallel threads. |
| `--output` | `-o` | `output/` | Directory where results will be saved. |

---

## 📊 Output Files

The script generates two files in the `output/` directory:

### 1. Summary Report (`summary_TIMESTAMP.txt`)

A clean list of keys that passed at least one profile, showing exactly what they are capable of.

> **Example:**
> ```text
> KEY: sk-proj-xxxx...
> MODELS TOTAL: 42
>   [+] Profile: gpt-4o (ACTIVE) | Extras Found: ['dall-e-3', 'whisper-1']
>   [+] Profile: gpt-4o-mini (ACTIVE) | Extras Found: ['gpt-3.5-turbo']
> 
> ```
> 
> 

### 2. Detailed Data (`results_TIMESTAMP.json`)

A full programmatic export of every key, including those that failed, containing full error messages and raw model counts. Use this for importing into other databases or tools.


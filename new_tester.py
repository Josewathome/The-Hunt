import os
import time
import json
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()
console_lock = threading.Lock()

def check_api_key_against_config(api_key: str, check_configs: list, thread_id: int = 0) -> dict:
    """
    Checks one key against the entire list of primary/extra pairs.
    """
    if api_key.lower().startswith("bearer "):
        api_key = api_key.split(" ", 1)[1]

    client = OpenAI(api_key=api_key)
    
    # Structure to hold results for this specific key
    key_result = {
        "key": api_key,
        "is_valid": False,
        "total_models_available": 0,
        "passes": [], # List of configurations it passed
        "errors": []
    }

    try:
        # 1. Fetch Metadata once per key to save time
        models_resp = client.models.list()
        all_ids = [m.id for m in models_resp.data]
        key_result["is_valid"] = True
        key_result["total_models_available"] = len(all_ids)

        # 2. Loop through each profile in the config
        for config in check_configs:
            primary = config["primary_model"]
            extras = config["extras"]
            
            # Check if primary model even exists in metadata
            if any(primary in mid for mid in all_ids):
                try:
                    # LIVE TEST: Attempt completion
                    client.chat.completions.create(
                        model=primary,
                        messages=[{"role": "user", "content": "i"}],
                        max_tokens=1
                    )
                    
                    # If we reach here, the live test passed
                    found_extras = [ex for ex in extras if any(ex in mid for mid in all_ids)]
                    key_result["passes"].append({
                        "profile": primary,
                        "found_extras": found_extras
                    })
                except Exception as e:
                    key_result["errors"].append(f"Primary {primary} failed live test: {str(e)[:50]}")
            
        with console_lock:
            status_msg = f"[green]PASS: {len(key_result['passes'])} profiles[/green]" if key_result["passes"] else "[yellow]VALID but no profiles passed[/yellow]"
            console.print(f"[Thread {thread_id}] {api_key[:8]}... | {status_msg}")

    except Exception as e:
        key_result["is_valid"] = False
        with console_lock:
            console.print(f"[red][Thread {thread_id}] ❌ {api_key[:8]}... INVALID KEY[/red]")
            
    return key_result

def run_scanner(key_file, config_file, workers, output_dir):
    # Load Keys
    if not os.path.exists(key_file):
        console.print(f"[red]Key file {key_file} not found[/red]")
        return
    with open(key_file, 'r') as f:
        keys = [line.strip() for line in f if line.strip()]

    # Load Config
    if not os.path.exists(config_file):
        console.print(f"[red]Config file {config_file} not found[/red]")
        return
    with open(config_file, 'r') as f:
        check_configs = json.load(f)

    all_results = []

    with Progress(TextColumn("[bold blue]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
        task = progress.add_task("Multi-Profile Scan...", total=len(keys))
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(check_api_key_against_config, key, check_configs, i % workers): key for i, key in enumerate(keys)}
            for future in as_completed(futures):
                all_results.append(future.result())
                progress.advance(task)

    # SAVING RESULTS
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Save Full JSON Detail
    json_path = os.path.join(output_dir, f"results_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    # 2. Save Readable Summary
    txt_path = os.path.join(output_dir, f"summary_{timestamp}.txt")
    with open(txt_path, 'w') as f:
        f.write(f"OPENAI MULTI-CHECK REPORT - {timestamp}\n" + "="*50 + "\n")
        for res in all_results:
            if res["passes"]:
                f.write(f"KEY: {res['key']}\n")
                f.write(f"MODELS TOTAL: {res['total_models_available']}\n")
                for p in res["passes"]:
                    f.write(f"  [+] Profile: {p['profile']} (ACTIVE) | Extras Found: {p['found_extras']}\n")
                f.write("-" * 30 + "\n")

    console.print(Panel(f"Scan Complete!\n[green]JSON Results:[/green] {json_path}\n[blue]Text Summary:[/blue] {txt_path}"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", default="keys.txt")
    parser.add_argument("--config", "-c", default="config.json")
    parser.add_argument("--workers", "-w", type=int, default=10)
    parser.add_argument("--output", "-o", default="output")
    args = parser.parse_args()

    run_scanner(args.file, args.config, args.workers, args.output)
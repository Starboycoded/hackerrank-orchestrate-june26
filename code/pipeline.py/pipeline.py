"""Core pipeline: loads data, processes each claim through Claude, produces output.csv.
Includes --dry-run mode to inspect prompts without API calls."""

import json, time, base64, os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from config import model_config
from prompts import SYSTEM_PROMPT, build_user_message


def load_csv(filepath: str) -> pd.DataFrame:
    return pd.read_csv(filepath)


def load_user_history(filepath: str) -> Dict[str, Dict]:
    df = pd.read_csv(filepath)
    return {row["user_id"]: row.to_dict() for _, row in df.iterrows()}


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".gif":"image/gif",".webp":"image/webp"}.get(ext,"image/jpeg")


def call_claude(system_prompt, user_text, image_paths, api_key, model):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    content = []
    for img_path in image_paths:
        b64 = encode_image(img_path)
        mime = get_image_mime(img_path)
        content.append({"type":"image","source":{"type":"base64","media_type":mime,"data":b64}})
    content.append({"type":"text","text":user_text})
    response = client.messages.create(model=model, max_tokens=1500, system=system_prompt,
        messages=[{"role":"user","content":content}], temperature=0.1)
    return {"content":response.content[0].text,"input_tokens":response.usage.input_tokens,"output_tokens":response.usage.output_tokens}


def call_openai(system_prompt, user_text, image_paths, api_key, model):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    content = [{"type":"text","text":user_text}]
    for img_path in image_paths:
        b64 = encode_image(img_path)
        mime = get_image_mime(img_path)
        content.append({"type":"image_url","image_url":{"url":f"data:{mime};base64,{b64}","detail":"high"}})
    response = client.chat.completions.create(model=model,
        messages=[{"role":"system","content":system_prompt},{"role":"user","content":content}],
        max_tokens=1500, temperature=0.1)
    return {"content":response.choices[0].message.content,"input_tokens":response.usage.prompt_tokens,"output_tokens":response.usage.completion_tokens}


def parse_json_response(content):
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"): lines = lines[1:]
        if lines and lines[-1].strip()=="```": lines = lines[:-1]
        text = "\n".join(lines)
    start = text.find("{")
    end = text.rfind("}")
    if start!=-1 and end!=-1: text = text[start:end+1]
    try: return json.loads(text)
    except json.JSONDecodeError: return None


OUTPUT_COLUMNS = ["user_id","image_paths","user_claim","claim_object",
    "evidence_standard_met","evidence_standard_met_reason","risk_flags",
    "issue_type","object_part","claim_status","claim_status_justification",
    "supporting_image_ids","valid_image","severity"]


def fallback_result(claim_row, reason):
    return {"user_id":claim_row.get("user_id",""),"image_paths":claim_row.get("image_paths",""),
        "user_claim":claim_row.get("user_claim",""),"claim_object":claim_row.get("claim_object",""),
        "evidence_standard_met":"false","evidence_standard_met_reason":reason[:150],
        "risk_flags":"none","issue_type":"unknown","object_part":"unknown",
        "claim_status":"not_enough_information","claim_status_justification":reason[:250],
        "supporting_image_ids":"none","valid_image":"false","severity":"unknown"}


def process_claim(claim_row, user_history, image_base_dir, dry_run=False):
    provider = model_config.get_provider()
    user_id = claim_row.get("user_id","")
    user_hist = user_history.get(user_id)
    user_message = build_user_message(claim_row, user_hist)
    image_paths_raw = claim_row.get("image_paths","")
    rel_paths = [p.strip() for p in image_paths_raw.split(";") if p.strip()]
    resolved_paths = []
    for rel in rel_paths:
        full = Path(image_base_dir)/rel
        if not full.exists(): full = Path(rel)
        if full.exists(): resolved_paths.append(str(full))

    if not resolved_paths:
        return fallback_result(claim_row,"No image files could be loaded."),{"input_tokens":0,"output_tokens":0}

    if dry_run:
        est_image_tokens = len(resolved_paths)*1600
        est_text_tokens = len(user_message.split())*1.3
        est_total = int(est_image_tokens+est_text_tokens+1000)
        print(f"\n    DRY RUN user={user_id}")
        print(f"    Images: {len(resolved_paths)} ({', '.join(Path(p).name for p in resolved_paths)})")
        print(f"    Est. tokens: ~{est_total}")
        return fallback_result(claim_row,"DRY_RUN"),{"input_tokens":est_total,"output_tokens":0}

    for attempt in range(model_config.max_retries):
        try:
            if provider=="anthropic":
                result = call_claude(SYSTEM_PROMPT,user_message,resolved_paths,
                    model_config.anthropic_api_key,model_config.anthropic_model)
            elif provider=="openai":
                result = call_openai(SYSTEM_PROMPT,user_message,resolved_paths,
                    model_config.openai_api_key,model_config.openai_model)
            else: raise ValueError(f"Unsupported: {provider}")
            parsed = parse_json_response(result["content"])
            if parsed:
                output = {"user_id":user_id,"image_paths":image_paths_raw,
                    "user_claim":claim_row.get("user_claim",""),"claim_object":claim_row.get("claim_object",""),
                    "evidence_standard_met":str(parsed.get("evidence_standard_met","false")).lower(),
                    "evidence_standard_met_reason":str(parsed.get("evidence_standard_met_reason",""))[:150],
                    "risk_flags":str(parsed.get("risk_flags","none")),
                    "issue_type":str(parsed.get("issue_type","unknown")),
                    "object_part":str(parsed.get("object_part","unknown")),
                    "claim_status":str(parsed.get("claim_status","not_enough_information")),
                    "claim_status_justification":str(parsed.get("claim_status_justification",""))[:250],
                    "supporting_image_ids":str(parsed.get("supporting_image_ids","none")),
                    "valid_image":str(parsed.get("valid_image","true")).lower(),
                    "severity":str(parsed.get("severity","unknown"))}
                if output["valid_image"]=="false":
                    output["evidence_standard_met"]="false"
                return output,{"input_tokens":result["input_tokens"],"output_tokens":result["output_tokens"]}
            time.sleep(model_config.retry_delay)
        except Exception as e:
            if attempt<model_config.max_retries-1: time.sleep(model_config.retry_delay*(attempt+1))

    return fallback_result(claim_row,f"Failed after {model_config.max_retries} attempts"),{"input_tokens":0,"output_tokens":0}


def run_pipeline(claims_csv, user_history_csv, image_base_dir, output_csv, dry_run=False, limit=0):
    claims_df = pd.read_csv(claims_csv)
    if limit>0: claims_df = claims_df.head(limit)
    user_history = load_user_history(user_history_csv)
    results = []; total_input=0; total_output=0; calls=0
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}\nMulti-Modal Evidence Review - {mode}\nClaims: {len(claims_df)}\n{'='*60}\n")
    for idx,(_,row) in enumerate(claims_df.iterrows()):
        print(f"[{idx+1}/{len(claims_df)}] user={row['user_id']} obj={row['claim_object']:7s}",end="",flush=True)
        result,usage = process_claim(row.to_dict(),user_history,image_base_dir,dry_run=dry_run)
        results.append(result)
        total_input+=usage["input_tokens"]
        total_output+=usage["output_tokens"]
        calls+=1
        if not dry_run:
            print(f" -> {result['claim_status'].upper():<22s} vi={'Y' if result['valid_image']=='true' else 'N'} es={'Y' if result['evidence_standard_met']=='true' else 'N'} | {result['issue_type']:<16s} | {result['object_part']}")
        else:
            print("")
    output_df = pd.DataFrame(results)
    for col in OUTPUT_COLUMNS:
        if col not in output_df.columns: output_df[col]="unknown"
    output_df = output_df[OUTPUT_COLUMNS]
    if not dry_run: output_df.to_csv(output_csv,index=False)
    print(f"\n{'='*60}\nCalls: {calls} | Tokens: {total_input+total_output:,}\n{'='*60}\n")
    return output_df

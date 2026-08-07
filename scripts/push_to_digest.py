def main():
    token = get_env_or_die("DIGEST_REPO_TOKEN")
    push_count = int(os.environ.get("PUSH_COUNT", "2"))

    # ✅ 確保 state 檔案一開始就存在
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        STATE_PATH.write_text('{"last_pushed_index":0}', encoding="utf-8")

    v3_order = load_v3_order()
    if not v3_order:
        print("No social-posts folders found, nothing to sync.")
        return

    schedule_lookup = load_schedule_lookup()

    state = {"last_pushed_index": 0}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))

    start = state["last_pushed_index"]
    batch = v3_order[start:start + push_count]
    if not batch:
        print("All pieces already synced to digest.")
        return

    pushed = 0
    for num, slug in batch:
        entry = schedule_lookup.get(slug)
        if not entry:
            print(f"WARN: no schedule.json entry found for slug '{slug}', skipping")
            continue
        v3_entry = dict(entry)
        v3_entry["sequence"] = num
        print(f"Pushing #{num} {entry['topic_folder']} to digest...")
        try:
            push_schedule_entry(token, v3_entry)
            push_copy_md(token, entry["topic_folder"])
            push_images_manifest(token, entry["topic_folder"], entry.get("images_present", []))
            pushed += 1
        except RuntimeError as e:
            print(f"ERROR: {e}")
            break  # 遇到錯誤就停止，但後面的 state 寫入仍會執行

    state["last_pushed_index"] = start + pushed
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Synced {pushed} piece(s). last_pushed_index={state['last_pushed_index']}")

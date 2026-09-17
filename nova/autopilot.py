"""Nova AI training autopilot.

Runs resumable pretraining chunks, then post-training stages when the target
pretraining budget is reached. Designed for free notebook runtimes with
periodic termination. No quota bypassing or credential handling is performed.
"""
import argparse, math, subprocess, sys
from pathlib import Path


def run(cmd):
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True).returncode


def ckpt(path):
    import torch
    return torch.load(path, map_location="cpu")


def resolve_steps(token_budget, block_size, batch_size, grad_accum, world):
    tokens_per_step = block_size * batch_size * grad_accum * max(1, world)
    return max(1, math.ceil(token_budget / tokens_per_step)), tokens_per_step


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='HuggingFaceFW/fineweb_100BT')
    ap.add_argument('--pretrain-steps', type=int, default=None,
                    help='Explicit optimizer steps. Overrides --pretrain-tokens.')
    ap.add_argument('--pretrain-tokens', type=int, default=50_000_000,
                    help='Target training tokens; default is a practical free-compute budget.')
    ap.add_argument('--chunk-seconds', type=int, default=13200, help='Stop cleanly before notebook timeout.')
    ap.add_argument('--checkpoint', default='checkpoints/nova-stream.pt')
    ap.add_argument('--tokenizer-chars', type=int, default=5_000_000)
    ap.add_argument('--sft-steps', type=int, default=1500)
    ap.add_argument('--pref-steps', type=int, default=400)
    ap.add_argument('--do-posttrain', action='store_true')
    ap.add_argument('--allow-cpu', action='store_true', help='Allow CPU training instead of failing fast on a notebook without a GPU.')
    ap.add_argument('--prepare-posttrain', action='store_true', help='Fetch bounded open instruction/math/code data when post-training begins.')
    args = ap.parse_args()
    ck = Path(args.checkpoint)
    ck.parent.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        n_gpu = torch.cuda.device_count()
    except Exception:
        n_gpu = 0
    if n_gpu == 0 and not args.allow_cpu:
        raise SystemExit('No CUDA GPU detected. Start a GPU runtime; pass --allow-cpu only for a deliberate local smoke run.')

    block_size, batch_size, grad_accum = 1024, 2, 16
    pretrain_steps, tokens_per_step = resolve_steps(
        args.pretrain_tokens, block_size, batch_size, grad_accum, n_gpu or 1
    )
    if args.pretrain_steps is not None:
        pretrain_steps = args.pretrain_steps

    current = 0
    if ck.exists():
        current = int(ckpt(ck).get('step', 0))
    print(f'TARGET_PRETRAIN_STEPS={pretrain_steps} TOKENS_PER_STEP={tokens_per_step:,} TARGET_TOKENS~{pretrain_steps*tokens_per_step:,}', flush=True)

    if current < pretrain_steps:
        base = [sys.executable, 'train_hf_stream.py', '--dataset', args.data,
                '--steps', str(pretrain_steps), '--max-seconds', str(args.chunk_seconds),
                '--tokenizer-chars', str(args.tokenizer_chars), '--checkpoint-every', '50',
                '--layers', '8', '--heads', '8', '--kv-heads', '4', '--embd', '512',
                '--block-size', str(block_size), '--vocab-size', '8192', '--batch-size', str(batch_size),
                '--grad-accum', str(grad_accum), '--out', str(ck), '--grad-checkpoint']
        if ck.exists():
            base += ['--resume', str(ck)]
        print(f'Using {n_gpu} GPU(s); DDP={n_gpu > 1}', flush=True)
        cmd = ([sys.executable, '-m', 'torch.distributed.run', '--standalone',
                '--nproc_per_node', str(n_gpu)] + base[1:] if n_gpu > 1 else base)
        run(cmd)
        current = int(ckpt(ck).get('step', 0))

    if not args.do_posttrain or current < pretrain_steps:
        print(f'PRETRAIN_PROGRESS={current}/{pretrain_steps}; resume next session.', flush=True)
        return

    if args.prepare_posttrain or not Path('data/instructions_all.jsonl').exists():
        run([sys.executable, 'prepare_posttraining.py'])
    sft = Path('checkpoints/nova-instruct.pt')
    sft_data = Path('data/instructions_all.jsonl') if Path('data/instructions_all.jsonl').exists() else Path('data/instructions.jsonl')
    run([sys.executable, 'instruction_tune.py', '--checkpoint', str(ck), '--data', str(sft_data), '--steps', str(args.sft_steps), '--out', str(sft), '--checkpoint-every', '100'])
    pref = Path('checkpoints/nova-preference.pt')
    pref_data = Path('data/preferences_hf.jsonl') if Path('data/preferences_hf.jsonl').exists() else Path('data/preferences.jsonl')
    run([sys.executable, 'preference_tune.py', '--checkpoint', str(sft), '--data', str(pref_data), '--steps', str(args.pref_steps), '--out', str(pref), '--checkpoint-every', '50'])
    run([sys.executable, 'evaluate_suite.py', '--checkpoint', str(pref)])
    run([sys.executable, 'evaluate_capabilities.py', '--checkpoint', str(pref)])
    final = Path('checkpoints/nova-final.pt')
    import shutil
    shutil.copy2(pref, final)
    pref_tok = Path(str(pref).replace('.pt', '.tokenizer.json'))
    if pref_tok.exists():
        shutil.copy2(pref_tok, Path(str(final).replace('.pt', '.tokenizer.json')))
    print(f'NOVA_AUTOPILOT_COMPLETE final={final}', flush=True)


if __name__ == '__main__':
    main()

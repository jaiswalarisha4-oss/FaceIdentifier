# FaceIdentifier

A pipeline that takes a face scan, finds a real matching post about that
face on the web/social media, and anchors tamper-evident proof of the
discovery on a blockchain — end to end, with a standalone tool anyone can
use to re-verify the result later without trusting the original run.

```
face scan  →  face detection & encoding  →  genuine reverse-image / social search
           →  perceptual-hash match confirmation
           →  Merkle-batched, privacy-preserving blockchain anchor
```

## What it does

1. **Face identification** (`src/face_encoder.py`) — detects a face in the
   input image and extracts a 128-dimension embedding using
   [`face_recognition`](https://github.com/ageitgey/face_recognition)
   (dlib's ResNet face encoder).

2. **Web / social media search** (`src/social_search.py`) — sends the
   image to **Google Cloud Vision's Web Detection API** for a genuine
   reverse image search (this is a real HTTP call on every run, not a
   cached or hardcoded result), then filters the returned pages down to
   known social platforms (Instagram, X/Twitter, Facebook, TikTok, Reddit,
   LinkedIn, Pinterest, YouTube).
   > This project originally targeted Bing's Visual Search API, but
   > Microsoft retired the Bing Search API family (Web/Image/Visual
   > Search) on August 11, 2025. Google Cloud Vision's Web Detection is
   > the still-live equivalent used here instead.

3. **Match confirmation** (`src/perceptual_hash.py`) — search engines can
   return pages that merely *mention* an image, not pages that show it. Each
   candidate's thumbnail is perceptual-hashed (`pHash`) and compared against
   the input photo; only candidates above a similarity threshold (default
   `0.75`) are accepted as a genuine match, so the pipeline can't be fooled
   into anchoring an unrelated page.

4. **Blockchain verification** (`src/pipeline.py`, `src/merkle.py`,
   `src/simulated_chain.py`, `src/testnet_chain.py`,
   `contracts/FaceProofRegistry.sol`) — see **Unique feature** below.

## Unique feature: privacy-preserving, Merkle-batched anchoring

Most "put it on the blockchain" projects hash one record and write it
directly on-chain. That has two problems that matter specifically for a
*face-recognition* project: it puts biometric-adjacent data on a public,
permanent ledger, and it makes every discovery cost its own gas fee. This
project is built around avoiding both:

- **The raw face embedding never leaves the machine, and never touches the
  chain.** Only `sha256(salt + embedding)` is stored — a one-way,
  salted fingerprint. You can prove "this scan matches that scan" without
  ever exposing or reconstructing the biometric data itself, which matters
  given how face embeddings are increasingly treated as regulated
  biometric data (GDPR/BIPA-style rules).

- **Evidence is batched through a Merkle tree; only the 32-byte root goes
  on-chain.** `src/merkle.py` implements a standard SHA-256 Merkle tree.
  Every discovery becomes a leaf; a single transaction anchors the root for
  the whole batch. This is the same trick rollups and timestamping services
  use to make on-chain writes cheap and scalable — one hackathon demo run
  might be one leaf, but the architecture is ready for thousands.

- **Independent, offline re-verification.** `scripts/verify_record.py`
  doesn't trust the database — it recomputes the evidence hash from
  scratch, rebuilds the Merkle proof, and checks it against whatever the
  chain (real or simulated) actually has on record. Anyone with the
  evidence file and read access to the chain can run this themselves; nothing
  about verification depends on the original tool or its author.

- **Chain-agnostic by design.** The same pipeline anchors to a real
  EVM-compatible testnet/mainnet contract (`src/testnet_chain.py` +
  `contracts/FaceProofRegistry.sol`) when credentials are configured, or
  falls back automatically to a local, tamper-evident simulated chain
  (`src/simulated_chain.py`) when they aren't — so the whole pipeline can be
  demoed fully offline, with zero cost and zero setup, and then pointed at
  a real chain later by setting three environment variables.

## Which blockchain

The pipeline targets **any EVM-compatible chain** via a small Solidity
registry contract (`contracts/FaceProofRegistry.sol`) and `web3.py`. It was
built and tested against:

- **Polygon Amoy testnet** (recommended — fast, free faucet, low friction)
- Works identically on **Ethereum Sepolia**, a local **Anvil/Ganache** node,
  or mainnet — only the `RPC_URL` / `PRIVATE_KEY` / `CONTRACT_ADDRESS`
  environment variables change.

If those variables aren't set, the pipeline automatically uses the
**built-in simulated chain** (`src/simulated_chain.py`): a local,
proof-of-work-linked, tamper-evident block store persisted to `chain.json`.
It provides the same guarantee a real chain does for this project's
purposes — any edit to historical data is detectable — without requiring a
wallet, funds, or network access, which is what makes the whole pipeline
demoable end-to-end offline.

## How to run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

`face_recognition` depends on `dlib`, which needs `cmake` and a C++
toolchain to build. On Debian/Ubuntu:

```bash
sudo apt-get install -y cmake build-essential
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

- `GOOGLE_VISION_API_KEY` is **required** for the search step. To get one:
  1. Go to [console.cloud.google.com](https://console.cloud.google.com/) and sign in (create a project if you don't have one — project dropdown → **New Project**).
  2. **APIs & Services → Library** → search **Cloud Vision API** → **Enable**.
  3. **APIs & Services → Credentials → Create Credentials → API key** — copy the key it generates.
  4. (Recommended) Click the new key → **API restrictions** → restrict it to **Cloud Vision API** only.
  5. Google may prompt you to attach a billing account to activate the API — the Web Detection feature used here has a free tier of 1,000 units/month, so a hackathon demo won't be charged; set a budget alert if you want a safety net.
- `RPC_URL` / `PRIVATE_KEY` / `CONTRACT_ADDRESS` are **optional** — leave
  them blank to use the simulated chain.

### 3. (Optional) Deploy the contract to a real testnet

```bash
python scripts/deploy_contract.py
```

Prints the deployed address — put it in `CONTRACT_ADDRESS` in `.env`.

### 4. Run the pipeline

```bash
python scripts/run_pipeline.py --image path/to/face_scan.jpg
```

This prints the full result: the evidence record, its Merkle root, the
proof, and where it was anchored (a testnet transaction hash, or a
simulated-chain block).

### 5. Re-verify independently

```bash
python scripts/verify_record.py --evidence-index 0
```

Recomputes the evidence hash from `evidence_store.json` and checks it
against the on-chain (or simulated-chain) record, entirely independently of
the run that created it.

### Run the test suite

The Merkle tree, simulated chain, and perceptual-hash logic are covered by
unit tests that don't require network access or the heavier face/vision
dependencies:

```bash
pytest tests/
```

## Project layout

```
contracts/
  FaceProofRegistry.sol      Solidity registry: merkleRoot -> (submitter, timestamp, metadataURI)
  FaceProofRegistry.abi.json Precompiled ABI used by testnet_chain.py
src/
  face_encoder.py            Face detection + 128-d embedding
  social_search.py           Google Cloud Vision reverse-image search
  perceptual_hash.py         pHash-based match confirmation
  merkle.py                  SHA-256 Merkle tree (build / prove / verify)
  simulated_chain.py         Local tamper-evident fallback chain
  testnet_chain.py           web3.py anchor/verify against a real chain
  evidence_store.py          Off-chain evidence metadata store
  pipeline.py                Orchestrates the full flow
scripts/
  run_pipeline.py            CLI: run the end-to-end pipeline
  verify_record.py           CLI: standalone re-verification
  deploy_contract.py         CLI: compile + deploy the registry contract
tests/                       Unit tests (merkle, simulated chain, pHash)
```

## Known limitations

- **Search coverage depends on Google's index.** Reverse image search only
  surfaces posts that Google has actually crawled and indexed; a very
  recent or low-visibility post may not appear. No reverse-image search
  API can guarantee finding every matching post on the web.
- **Perceptual hashing, not face verification, gates the match.** The
  pHash comparison confirms the *search-result image* looks like the input
  photo; it does not re-run face recognition on every candidate. A page
  with a visually similar but different face could, in principle, pass the
  similarity threshold — raising `--threshold` tightens this at the cost of
  more false negatives.
- **The simulated chain is a local demo, not a distributed ledger.** It
  gives the same tamper-evidence guarantee (any edited block is detectable)
  but no external party can independently query it the way they could a
  public chain — use the real testnet/mainnet mode for a genuinely
  third-party-verifiable record.
- **One evidence record per pipeline run is anchored as its own
  single-leaf Merkle tree** in this demo for simplicity; batching multiple
  runs into one multi-leaf tree/transaction is supported by `merkle.py` but
  not wired up as a scheduled batch job.
- **No consent/authorization check is enforced on the input photo.** This
  tool is intended for auditing your own public footprint; it does not
  verify that the person submitting the photo is the person in it.

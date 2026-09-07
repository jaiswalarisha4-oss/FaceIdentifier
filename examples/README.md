# Examples

No sample face images are bundled with this repository on purpose — shipping
real or stock face photos in a public repo about biometric matching is
exactly the kind of casual data exposure this project's design tries to
avoid (see the "Unique feature" section of the root README).

To try the pipeline yourself:

1. Drop any photo containing a clear, front-facing face into this folder,
   e.g. `examples/my_face.jpg` (git-ignored by default — see `.gitignore`).
2. Run:
   ```bash
   python scripts/run_pipeline.py --image examples/my_face.jpg
   ```

Use a photo you have the rights to use for a reverse-image search — ideally
one of yourself, since the pipeline is meant to search for *your own*
public footprint, not to look someone else up without consent.

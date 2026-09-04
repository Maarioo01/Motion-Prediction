# Build gotchas

Real issues hit while getting these 10 repos to build and run, kept here because the
same root causes will very likely recur on any new repo added to this project. See the
main [README](../README.md) for the "adding a repo" workflow these apply to.

- **GPU1 (the 3090 Ti) is unreliable and disabled by policy** — see the README's "GPU
  allocation" section for the full story. The infra-relevant part: once GPU1 wedges
  (`nvidia-smi` reports `Unable to determine the device handle: Unknown Error`),
  **every** GPU container launch fails, not just ones requesting GPU1 — confirmed that
  `docker run --gpus '"device=0"'` fails identically to `--gpus all` while GPU1 is
  wedged, because `nvidia-container-cli` enumerates all GPUs on the system as part of
  its own detection step regardless of which one you actually asked for. If you hit
  `nvidia-container-cli: detection error: nvml error: unknown error`, check `nvidia-smi`
  for GPU1's state before assuming it's a Docker/config problem - it very likely isn't.
  Recovery is `sudo nvidia-smi -r -i 1` (targeted, no reboot needed).
- **CUDA 11.x's `nvcc` refuses any host gcc newer than what that CUDA release
  supports** (e.g. cu11.8 rejects gcc>11 with "gcc versions later than 11 are not
  supported"). The `continuumio/miniconda3` base image (Debian bookworm) ships gcc-12,
  which silently breaks any CUDA extension compiled against a conda-installed
  `cuda-toolkit`. Fix: `conda install -c conda-forge gcc=11 gxx=11` (or whatever ceiling
  that specific CUDA version needs) so it takes PATH priority over the system compiler.
  Match the override to the *specific* CUDA version's actual compiler ceiling, not a
  single fixed "gcc=11" recipe — see the UniAD note below for the counter-example.
- **`docker build` has no GPU attached**, so any package whose setup.py gates its CUDA
  build on live `torch.cuda.is_available()` (not just an arch-list env var) will silently
  produce a CPU-only build with no error — it just warns at *runtime* instead ("NATTEN was
  not built with cuda support"). Always check the specific package's setup.py for its own
  force-CUDA env var (NATTEN: `FORCE_CUDA=1` + `NATTEN_CUDA_ARCH=8.6`; others vary) rather
  than assuming an arch-list variable alone is sufficient.
- **PEP 517 build isolation** breaks packages whose setup.py does `import torch` at build
  time (NATTEN, and likely others) — pip's isolated build env doesn't see the
  already-installed torch. Fix: `pip install --no-build-isolation <pkg>`.
- **setuptools ≥81 dropped `pkg_resources`**, which older `torch.utils.cpp_extension.py`
  (torch ≤2.1-ish) still imports from. Pin `setuptools==69.5.1` before compiling anything
  against an older torch.
- **Installing extra `requirements.txt` *after* a pinned `pip install torch==X+cuY`** can
  silently swap it for a different torch build (PyPI's default cu121-bundled wheel) if any
  other package in that file has an unpinned `torch` dependency — pip's resolver doesn't
  reliably keep a local-version-tagged package pinned across separate installs. Always
  install the exact pinned torch/torchvision/torchaudio triplet **last**, and verify after
  with `pip check`.
- **Even installing the pinned torch triplet last isn't always enough**: if something
  earlier (e.g. `pytorch-lightning`/`lightning`'s own unpinned `torch` dependency)
  happens to resolve to the exact same *bare* version string (e.g. `2.0.1`) from
  default PyPI (a different CUDA build, shown with no `+cuXXX` suffix), pip considers
  the later pinned `torch==2.0.1` request "already satisfied" and silently skips
  reinstalling it — while torchvision/torchaudio *do* get freshly installed from the
  cu-specific index, leaving mismatched CUDA builds ("PyTorch and torchvision were
  compiled with different CUDA versions"). Fix: pin the **explicit local version**
  everywhere, e.g. `torch==2.0.1+cu118` not just `torch==2.0.1` — this can't silently
  match a differently-tagged build. Always verify post-build with a real forward pass
  or at least `python -c "import torch, torchvision; print(torch.__version__,
  torchvision.__version__)"`, not just that the image built.
- **git refuses to operate in a bind-mounted repo dir** owned by the host user while the
  container runs as root ("detected dubious ownership") — breaks any setup.py that shells
  out to `git rev-parse` for a version string. Fix: `git config --global --add
  safe.directory /workspace` in the entrypoint before anything else runs.
- **`opencv-python` needs `libGL.so.1`** (an X11/GUI library) which a minimal Docker
  image doesn't have — breaks on `import cv2` with no obvious reason from the pip
  install succeeding. Prefer `opencv-python-headless` when you control the pin directly;
  when it's pulled in transitively by something you don't control (e.g. `metadrive`, a
  ScenarioNet dependency, in UniTraj), just install `libgl1 libglib2.0-0 libxext6
  libxrender-dev` via apt instead.
- **Very old exact-pinned transitive dependencies** (e.g. argoverse-api's own
  `numpy==1.19`/`hydra-core==1.1.0`/`omegaconf==2.1.0`/`motmetrics==1.1.3`, some without
  even a resolvable wheel anymore) are often broader than what your actual code path
  uses. Trace the real import graph of the specific functions you call (not the whole
  package) before assuming you need the full, ancient `install_requires` — installing
  with `--no-deps` and supplying modern versions of just what's actually imported is
  often more reliable than fighting a 2021-era pin. Watch for it needing a bit more than
  first suspected once you actually run the code (a second, deeper import chain can pull
  in one more of the "unnecessary" old deps - just add it, unpinned, when it shows up).
- **Unpinned packages in a `requirements.txt` can silently backtrack to a wheelless
  ancient version** if another unrelated pin in the same file (e.g. an old exact
  `protobuf==` pin) constrains their dependency resolution — pip will keep trying older
  and older releases until it finds one whose own requirements fit, even if that means
  falling back to a pre-wheel sdist that then fails to build (`Could not find "cmake"
  executable!`). If you don't actually need the offending package for anything beyond an
  optional feature, just drop it; otherwise pin it explicitly to a version you know has
  a prebuilt wheel.
- **A wheel with malformed PEP 440 metadata** (e.g. `pytorch-lightning==1.8.2`'s
  `torch (>=1.9.*)` — an invalid `.*` with `>=`) makes pip ≥24.1 refuse to install it at
  all, even though the wheel itself is otherwise fine. Bump to the nearest patch release
  in the same minor line rather than downgrading pip project-wide.
- **When a repo ships its own official `docker/Dockerfile`, adapt it rather than
  reinventing one** (UniAD). It's a tested, working recipe for a notoriously rigid
  OpenMMLab pin (mmcv-full 1.4.0/mmdet 2.14.0/mmdet3d 0.17.1) — and explains gotchas
  you'd otherwise have to rediscover: UniAD's official image is Ubuntu 20.04-based,
  whose *native* apt gcc is gcc-9, which is what CUDA 11.1's nvcc happens to need — no
  gcc-version override required there, unlike our other Dockerfiles (Debian-bookworm
  based, gcc-12) which all need one for CUDA 11.x.
- **Python 3.7 is EOL, and its pain compounds** (hit hardest on CMP, the only repo
  pinned to 3.7): recent releases of many packages (`safetensors`, `cmake`, `cumm`,
  `pympler`) have dropped cp37 wheels entirely, so pip backtracks through the *entire*
  version history trying to satisfy a transitive constraint, often bottoming out on a
  decade-old sdist with its own packaging bugs (`No module named 'pip.req'`,
  `puccinialin` needing Python≥3.9). Each occurrence looked like a distinct bug but was
  the same root cause. Once you see backtracking messages ("pip is looking at multiple
  versions of X... this could take a while") stall for minutes, don't wait it out —
  kill the build and pin that package directly to a version with a known cp37 wheel;
  guessing-and-checking one at a time is slower than just pinning everything unpinned
  in the file up front once the pattern is recognized.
- **A dependency's own exact-pinned sub-dependency can contradict your own pin**: CMP's
  `environment.yml` pins `numpy==1.21.6`, but `waymo-open-dataset-tf-2.6.0` needs
  `tensorflow==2.6.0`, which needs `numpy~=1.19.2` — a real, unresolvable conflict pip
  reports explicitly (unlike the backtracking cases above). When pip prints "The
  conflict is caused by:", trust it and relax to whichever pin the narrowest
  transitive constraint demands, after checking the other packages only need `>=`.
- **A package can genuinely compile and be usable while a *verification* import still
  fails** (UniTraj): importing one submodule of a package (`unitraj.models.mtr.ops.knn`)
  runs that package's whole `__init__.py`, which cascaded into an unrelated bundled
  backbone (`fmae`) with its own upstream bug (a bare `from utils.submission_av2
  import ...` that only resolves when run as `cd unitraj && python train.py`, not as an
  installed package). Don't chase every downstream import error as an environment
  problem — check whether the specific thing you actually need (here: the compiled
  `.so` files, confirmed present on disk and loadable via `importlib` directly) works,
  and adjust any automated build-check (entrypoint.sh) to test that narrowly rather
  than importing through a fragile, unrelated cascade.
- Iterating on these fixes chews through disk fast (each Dockerfile change invalidates
  cache for everything after it). Run `docker builder prune -f` whenever `/` free space
  gets tight — it only removes unreferenced build cache, never the tagged images
  themselves. This reclaimed 200GB+ multiple times over the course of this project.
- **A working environment doesn't mean a repo's own code is bug-free** (SceneInformer,
  discovered trying to actually train it, not just import-check it): its
  `waymo_utils.py` calls `scenario.ParseFromString(bytearray(data.numpy()))`, which
  modern `protobuf` rejects (`TypeError: expected bytes, bytearray found`) - older
  protobuf accepted anything supporting the buffer protocol, current protobuf requires
  actual `bytes`. Fixed in place (`bytearray(...)` → `bytes(...)`, two call sites) since
  this is upstream source, not something a Dockerfile pin can fix. Also had a template
  config (`configs/scene_informer.yaml`) with literal unfilled `path: PATH`
  placeholders - `verify.sh`-style import checks won't catch either of these, only an
  actual training attempt will. Don't assume "the environment works" means "the repo's
  training path works" for anything not already covered by `verify.sh` or the Training
  Plan's Track A checkpoint validation.
- **`find_unused_parameters` errors under DDP** ("It looks like your LightningModule
  has parameters that were not used in producing the loss") happen when a model has
  conditional branches (SceneInformer's decoder has separate occlusion vs. observed
  heads, not all used on every batch) - fine on 1 GPU, breaks on ≥2 under plain DDP.
  Lightning's `Trainer(strategy="ddp_find_unused_parameters_true")` fixes it *when it
  applies* - moot here now that GPU1 is disabled, but the fix is real and worth knowing
  if multi-GPU on a healthy pair of cards is ever back on the table.

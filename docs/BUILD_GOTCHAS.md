# Build gotchas

Real issues hit while getting these 10 repos to build and run, kept here because the
same root causes will very likely recur on any new repo added to this project. See the
main [README](../README.md) for the "adding a repo" workflow these apply to.

- *(History: the 3090 Ti was replaced by an RTX 5090 on 2026-11-16; see "RTX 5090 / cu128 images" at the end.)*
  **GPU1 (the 3090 Ti) is unreliable and disabled by policy** — see the README's "GPU
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
- **`repos/` lives on the OS disk, not `/raid`** — easy to forget since every dataset
  mount in `docker-compose.yml` points at `/raid`, but a repo's own *preprocessing
  output* (unless a service explicitly mounts scratch space) lands in
  `repos/<Name>/data_staging/`, which is a normal directory under the git working tree,
  physically on `/dev/nvme0n1p2` (the ~930GB root disk `/`), not the 7.3TB `/raid`
  array. This machine's root disk had only **63GB free** (93% used, and most of the
  other ~600GB is unreadable-to-us usage under another user's `/home/guest` — not
  something to investigate or clean up) when SceneInformer's stage-1 preprocessing
  output alone reached 146GB, discovered right before what would have been a much
  larger stage-2 run — filling that disk on a headless remote machine risks the OS
  itself, not just the job. Fixed by moving each repo's `data_staging/` to
  `/raid/scratch/<name>_data_staging/` and adding a dedicated bind mount in
  `docker-compose.yml` (`/raid/scratch/<name>_data_staging:/workspace/data_staging`)
  that shadows the local path inside the container — every existing script/config
  keeps working unchanged since they all reference the same relative `data_staging/...`
  path, only where it physically lives changed. **Before starting any new large
  preprocessing run, check `df -h / /raid` first** — don't assume free space just
  because `/raid` has plenty.
- **A pipe to `tail` (or any downstream command) silently swallows the real exit
  code** — `docker compose run ... | tail -30` reports `tail`'s exit status (always 0),
  not the container's. Caught this the hard way: SceneInformer's stage-3
  `generate_dataset_summary.py` crashed with an unhandled `IndexError` on the very
  first invocation, but the piped command still reported "exited with code 0" and it
  looked like a clean run until the output directory turned out empty. Either check
  `${PIPESTATUS[0]}` (bash) after a piped command, or just don't pipe through `tail`
  when the exit code matters — let the full output land in the log file directly.
- **A rare data-dependent type bug can hide behind a 99.998% pass rate**
  (SceneInformer, `scripts/generate_dataset_summary.py`): `object_id_perspective` is
  stored as `float64` in the vast majority of the 114638 stage-2 output `.h5` files but
  `int64` in a few of them (an inconsistency from stage 2's own writer, not
  investigated further since it's cheap to work around at the read side) - the script
  reads `obj_idx = perspective_ids_tensor[t, perspective_idx]` and uses it directly as
  a fancy array index two lines later, which only works when it happens to be an
  integer dtype. Two lines below, `occluding_object_id` gets an explicit `int(...)`
  cast before the same kind of use - `obj_idx` just didn't, for no principled reason.
  Fixed by adding the same cast. Found by writing a throwaway parallel scan across all
  114638 files (`joblib.Parallel` + a copy of the loop wrapped in try/except) rather
  than guessing from the single stack trace, which named a scenario where `obj_idx`
  happened to equal the last valid row index — a red herring that looked like an
  off-by-one/out-of-bounds bug until the actual dtype was checked directly with
  `h5py`. Only 2 of 114638 files actually hit it, which is exactly the kind of bug a
  small-scale smoke test (a handful of files) will never surface - it only showed up
  running stage 3 against the real, full-scale stage-2 output.
- **A real training run's sample count can be very different from a naive estimate
  from raw preprocessing output** (SceneInformer): summing the raw
  positive/negative-sample index arrays from stage 3 suggested ~28M training
  examples; the actual `VectorizedDatasetHDF5` the trainer builds reported only 70541
  (7055 batches at batch_size 10) — the dataset class evidently doesn't map 1:1 onto
  the raw per-occlusion-event index count. Don't set something like
  `val_check_interval` from an estimate — always let the trainer report the real
  batch count first (Lightning's own error message states it directly:
  `` `val_check_interval` (10000) must be less than or equal to the number of the
  training batches (7055) ``) and size the config off that.
- **Launch anything meant to run for hours as a detached container, not a
  foreground/backgrounded shell command.** A `docker compose run` wrapped in a shell
  background task is still, underneath, a process this session's tooling is tracking —
  stopping that tracked task doesn't necessarily stop the container cleanly, and
  relying on it ties a long training run's fate to this session's own task-timeout
  bookkeeping. Use `docker compose run -d --rm <service> bash -c "<cmd> > <logfile>
  2>&1"` instead — the container runs independently of the launching shell, and
  progress is checked with `docker exec <container> tail -f <logfile>` (or `docker
  logs`) rather than reading a background task's captured output.
- **A real training run can OOM well into an epoch even when early batches fit fine**
  (SceneInformer): crashed with `torch.cuda.OutOfMemoryError` at step 2530/7055 of
  epoch 0 (36% in, after ~14 minutes of apparently-healthy training) - not a hardware
  issue, a genuine memory spike, most likely an unusually large scene (variable
  agent/object counts per sample, no fixed padding across the whole dataset, so peak
  memory isn't bounded by the average batch). The error message itself was
  informative: `18.96 GiB reserved in total by PyTorch` vs `14.46 GiB already
  allocated` - reserved much greater than allocated points at fragmentation, not just
  "batch too big." Fixed two ways together: dropped `batch_size` 10→6 for more safety
  margin against outlier-sized batches, and added `PYTORCH_CUDA_ALLOC_CONF=
  max_split_size_mb:128` (docker-compose.yml `environment:`) to reduce fragmentation,
  per PyTorch's own suggestion in the error text. **No progress was lost**: Lightning's
  `ModelCheckpoint` had already saved `last.ckpt` after the first validation pass (step
  2000, just before the crash at 2530) - resumed with `train_lightning.py -r
  <path-to-last.ckpt>`, which correctly fast-forwards through already-seen batches
  (visible as an artificially high it/s for the first several seconds - not a bug, it's
  skipping the forward/backward pass while resyncing dataloader position) before
  settling back into real training. Always check for a saved checkpoint before assuming
  a crashed run has to restart from scratch.
- **The protobuf `bytearray` vs `bytes` bug recurs per-repo, not just for SceneInformer**:
  MTR's own `mtr/datasets/waymo/data_preprocess.py` (the same script TrajFlow's was
  derived from) has the identical `scenario.ParseFromString(bytearray(data.numpy()))`
  call, and MTR's conda environment happens to pin a modern protobuf that rejects it
  (unlike TrajFlow's environment, confirmed earlier to use an older protobuf that
  accepts `bytearray` fine — same source code, different outcome, entirely dependent on
  which protobuf version each repo's Dockerfile happens to pull in). Fixed the same way:
  `bytearray(...)` → `bytes(...)`. Worth grepping for this exact pattern in any *new*
  repo that touches Waymo `scenario` protos before assuming it's fine just because a
  sibling repo with near-identical code didn't hit it.
- **MTR's `decode_map_features_from_proto` doesn't handle the `driveway` map feature
  type at all** — its `else: raise ValueError` fallback crashes on the very first
  scenario containing one. This is upstream code from 2022; `driveway` was evidently
  added to the Waymo dataset's map feature types in a later release than MTR's original
  implementation targeted. TrajFlow's derived script *does* handle it (has the
  `elif cur_data.driveway.ByteSize() > 0:` branch and a `TYPE_DRIVEWAY: 20` entry in
  `waymo_types.py`'s `polyline_type` dict) — ported both directly from there rather than
  inventing new values, so the numeric type ID matches across repos. A useful reminder
  that "the sibling repo already solved this" is worth checking before debugging from
  scratch, given how much of this code is copy-derived across repos in this bench.
- **Waymo `scenario` isn't one dataloader-agnostic format** (GameFormer): its
  `interaction_prediction/data_process.py` does `id_list[track.id]` for every id in
  `parsed_data.objects_of_interest`, keyed off `tracks_to_predict` — crashes
  (`KeyError: <id>`) the moment `objects_of_interest` isn't a subset of
  `tracks_to_predict`. Root cause wasn't a code bug so much as a data-format mismatch:
  the `training_20s` split (downloaded for SceneInformer's longer-horizon occlusion
  pipeline) has `tracks_to_predict` **always empty** — confirmed directly by parsing a
  few scenarios and printing both fields — while the standard `training`/`validation`/
  `testing` split has it populated (3-7 entries/scenario) as GameFormer's preprocessing
  expects. Patched `data_process.py` to skip ids not in `id_list` rather than crash
  (`docker/GameFormer/patches/data_process.py`), but that only stops the crash — pointed
  at `training_20s` it now runs clean and produces **zero output files** (every
  scenario's `tracks_list` is empty, so `interactive_process()` never populates
  `sdc_ids_list`). Verified against the real `validation` split instead (3 shards → 7403
  correctly-shaped `.npz` files) to confirm the fix is actually sound, not just
  crash-free. Lesson: a script running to completion with no exception is not the same
  as it doing anything — check that output actually landed, especially when swallowing
  a `KeyError` on data you haven't independently verified has the field you expect
  populated. See [`TRAINING_PLAN.md`](TRAINING_PLAN.md) and
  [`DATASETS.md`](DATASETS.md) for what this means for the still-missing plain
  `training` split.
- **QCNet: unpinned `av2` breaks on Python 3.8, and `verify.sh` couldn't see it.** The
  Dockerfile installed plain `av2`, which resolved to 0.3.1 - that release uses
  Python-3.9-only type-subscript syntax in `av2/utils/typing.py`
  (`TypeError: Type subscription requires python >= 3.9`), while QCNet's env is pinned to
  Python 3.8.16. `verify.sh`'s `import av2` passes anyway, because only deeper
  submodules trip it - the crash only appears on the first real training run. Pinned
  `av2==0.2.1`.
- **QCNet: `av2.map.map_api` needs `libGL.so.1`** (it imports `opencv-python`), which the
  minimal `miniconda3` base image doesn't have. Worse, QCNet's
  `datasets/argoverse_v2_dataset.py` wraps the av2 imports in `try/except ImportError`
  and silently substitutes `object` for each name, so the real error surfaces much later
  and makes no sense: `TypeError: object() takes no arguments` from `read_json_file(...)`.
  Fix: `libgl1` in the Dockerfile's apt list. Lesson: when an upstream repo swallows an
  `ImportError`, re-run the exact import block by hand before debugging anything else.
- **QCNet's dataset class assumes its own directory layout and a writable root.** By
  default it looks for `<root>/<split>/raw/<scenario_id>/` and
  `<root>/<split>/processed/*.pkl`, and if `raw/` isn't there it tries to download the
  split tarball from S3 *into `<root>`*. Our AV2 copy is `<root>/<split>/<scenario_id>/`
  (already the per-scenario layout it wants, just without the `raw/` level), mounted
  read-only, so it crashed trying to write `train.tar`. Fix: pass
  `--{train,val,test}_raw_dir /data/argoverse2/<split>` and point
  `--{train,val,test}_processed_dir` at `/workspace/data_staging/<split>_processed`, which
  `docker-compose.yml` bind-mounts from `/raid/scratch/qcnet_data_staging` (~48GB of
  `.pkl` caches for all three splits - keep it off the OS disk). Upstream `val.py` /
  `test.py` don't take these flags at all, hence `qcnet_inference.py` (see
  `docker/QCNet/extras/`).
- **QCNet at the paper's per-GPU batch size (4) runs out of memory on a 24GB card**, but only
  after ~7k steps, once a large enough scene (many agents, big map) shows up - the
  paper's "~160GB across 8x 3090" averages ~20GB per device, which leaves almost no
  headroom. `--train_batch_size 2` was stable for all 64 epochs (~21-23GB peak, ~5.5h
  per epoch on GPU0). `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` is **not** an
  option here: torch 2.0.1 rejects it at CUDA init (`Unrecognized CachingAllocator
  option`). Note the README's own caveat: matching the paper's numbers assumes a *total*
  batch size of 32 - see [`TRAINING_PLAN.md`](TRAINING_PLAN.md) for what training at 2
  actually cost.
- **tqdm progress bars in a redirected log file grow without bound** - every update is a
  `\r`-separated rewrite that a file keeps in full. QCNet's 64-epoch log reached several
  GB. Read such logs with `tr '\r' '\n' < log | tail`, and for long runs consider
  `--enable_progress_bar`-style flags or periodic truncation.

## V2X-Graph (added 2026-11-12, checklist B2)

- **README says Python 3.8, `requirements.txt` needs ≥ 3.10.** `scipy==1.15.3` and
  `Shapely==2.1.0` have no 3.8 wheels; the image uses 3.10 (torch 1.12.1+cu116 has cp310
  wheels). cu116 runs on the 3090 but not on a 5090 (sm_120 needs CUDA ≥ 12.8).
- **`pytorch_lightning==1.5.2` imports `pkg_resources`** → same setuptools gotcha as above;
  `setuptools==69.5.1` is pinned in the same pip call as the requirements.
- **argoverse-api (`--no-deps`) still needs 4 of its deps at import time**:
  `argoverse/utils/__init__.py` pulls `mpl_plotting_utils` etc. Found by importing every
  entry point (labels, dataset, model, `train`, `eval`, `maps_merge.py`): `descartes`,
  `imageio`, `omegaconf`, `colour`. Nothing else from its 2021 pin list is needed.
- **`dair_map_api` reads `$DATA_ROOT/map_files` at import time** (crashes with a
  `NoneType` path error if unset). `docker-compose.yml` sets
  `DATA_ROOT=/workspace/data_staging/tfd`; override with `-e DATA_ROOT=...` for V2X-Traj.
- **The released V2X-Seq-TFD doesn't match the layout the code expects.** Code reads
  `<view>/<split>/data/*.csv`, writes outputs next to the raw data, and reads a
  `v2x_fusion/` folder no released script creates (upstream issue #6: it is the
  vehicle-side trajectories). `extras/prepare_tfd_layout.sh` builds a writable symlink
  tree in `/raid/scratch/v2xgraph_data/tfd`. Note the two different roots: label
  generation and `maps_merge.py` take the TFD root, `preprocess.py`/`train.py`/`eval.py`
  take `<TFD root>/cooperative-vehicle-infrastructure`.
- **Checkpoints are Git LFS objects** (133-byte pointers after a plain clone) and the host
  has no `git-lfs`; the entrypoint fetches them on first start and chowns them back.
  Detecting pointers with `find -size -1k` silently fails: `find` rounds sizes *up* to
  whole KiB, so `-1k` only matches empty files. Use `-size -1024c`.
- **`traj_match_labels/` has its own `utils.py`** that shadows the top-level `utils.py`
  (which defines `TemporalData`). Run label generation from inside that folder, and the
  rest from the repo root, in separate processes.
- **Upstream `preprocess.py` is serial and was OOM-killed.** One process, ~3.5 s per
  scenario (≈ 35 h for TFD train + val), and it grew until the kernel killed it at the
  machine's 62 GB after ~870 val scenarios (`docker inspect` → `OOMKilled=true`). One
  scenario peaks at ~5.7 GB (with the merged 57k-lane map, `get_lane_features` builds a
  Python list of every lane-segment × agent pair before filtering by radius).
  `extras/preprocess_parallel.py` calls the same `process_argoverse` + `TemporalData` +
  `torch.save` per scenario, but with a process pool (`maxtasksperchild` recycles
  workers), atomic writes (tmp + rename) and the same skip-if-done resume rule. 6 workers
  ≈ 1 scenario/s at ~11 GB RSS. Also cap the container: `docker update --memory 48g
  --memory-swap 48g <container>`, so a spike kills the container, not the host.
  **Only for CPU-only jobs:** on this host (cgroup v2) `docker update` on a running
  container resets its device rules and the GPU disappears inside it (`You requested
  GPUs: [0] But your machine only has: []`). Run eval/training in a fresh container.
- **`utils.rowwise_in` is a dense O(|a|·|b|) broadcast.** It checks which agent-pair
  edges (~N²) are V2X pairs by materialising an `|a| × |b| × 2` tensor; one crowded val
  scenario asked for 128 GB (probably what OOM-killed the first serial run). The driver
  swaps it, in the dataset modules only, for an int64-key + `torch.isin` version:
  identical on 2000 random cases (`--selftest`) and on 40 real scenarios (byte-identical
  `.pt`). `train.py`/`eval.py` only load the caches, so they are unaffected.
- **Lane order in the `.pt` caches is not reproducible upstream.** Lane ids are strings
  collected in a Python `set`, so their order follows `PYTHONHASHSEED` (random per
  process). Two runs give the same values, permuted (`lane_vectors`, `lane_actor_index`,
  …). Harmless for the model (it aggregates over lanes), but run with
  `PYTHONHASHSEED=0` so caches are byte-reproducible. The first 878 val files (serial
  upstream run + a 6-scenario test) were made without it; kept, since they are only
  permuted, not different.
- **`TemporalData.__inc__` has the PyG 1.x signature but `requirements.txt` pins PyG
  2.6.1**, whose batching calls `__inc__(key, value, store)` → every `DataLoader` batch
  fails with `takes 3 positional arguments but 4 were given` (so `eval.py`/`train.py`
  don't run as released). `docker/V2X-Graph/patches/0001-temporaldata-inc-pyg2.patch`
  forwards `*args, **kwargs`; `setup.sh` applies it with `git apply` (idempotent).
  With it, the official TFD checkpoints reproduce the paper (`docs/RESULTS.md`).
- **The host has no `git-lfs`, so plain `git status`/`diff` in `repos/V2X-Graph` fails**
  (`git-lfs: not found`). Use `git -c filter.lfs.process= -c filter.lfs.required=false
  -c filter.lfs.smudge=cat -c filter.lfs.clean=cat ...`, or run git inside the container.
- **V2X-Traj: `V2XTrajDataset` reads a `v2x_test/` folder** that the release doesn't
  have; `process_argoverse` reads it as `ego_df` next to the infrastructure and vehicle
  views, so `extras/prepare_v2xtraj_layout.sh` links it to `ego-trajectories`. V2X-Traj
  ships its own prebuilt `map_files/` (byte-different from our merged TFD ones but the
  same 57,643 lanes with identical content; only the key order differs), so set
  `DATA_ROOT=/workspace/data_staging/v2x-traj` (the compose default points at TFD).
  History is 40 steps (4 s) + 40 future, not 50 + 50.
- **Upstream `train.py` hard-codes `seed_everything(2022)` and keeps only the top-5
  checkpoints by val minFDE.** The benchmark needs several seeds and the last checkpoint
  (no selection on val, see `docs/RESULTS.md`, "Protocol") → patch
  `0003-train-seed-arg-save-last.patch` adds `--seed` (default 2022, so upstream
  behaviour is unchanged) and a second `ModelCheckpoint(save_top_k=0, save_last=True,
  save_on_train_epoch_end=True)` that writes `checkpoints/last.ckpt` after every training
  epoch. Do not just add `save_last=True` to the monitored callback: that one only saves
  when validation runs (every 5 epochs), so `last.ckpt` would be from epoch 60 of 64, and a
  1-epoch run saves nothing.
- **Training was 6–8× slower than it needs to be.** `models/agent_lane_subgraph.py` looks
  up three lane-attribute tables (2, 4 and 2 rows) with ~690,000 indices per batch via
  `self.X_embed[idx]`; its backward is PyTorch's generic sort-based indexing backward, which
  serialises on the repeated rows and took 86 % of each step (profiled). Patch
  `0004-lane-embedding-fast-backward.patch` uses `F.embedding` (identical forward, gradient
  within float noise): 3090 1.24 → 5.91 steps/s, 5090 1.39 → 11.17 (`docs/RESULTS.md`,
  "Training speed"). Before it, the 5090 was only 13 % faster than the 3090 because the
  slow kernel does not scale with GPU size.
- **With 0004 the HDD cannot feed training** (5090: 3.54 steps/s from `/raid`, GPU mostly
  idle). The train graph files are therefore on the NVMe: `/home/baco/nvme_cache/v2xgraph/
  {tfd,v2xtraj}_train_processed`, and `.../train/processed` under `/raid/scratch/
  v2xgraph_data` are symlinks to them (the HDD originals are kept as `processed.hdd_backup`).
  The compose file mounts `/home/baco/nvme_cache` at the same path so the symlinks resolve
  inside containers. Val graph files stay on `/raid` (read once per evaluation).
- **The README's V2X-Traj "V2X" minFDE of 0.13 is a typo for 1.13**: the official
  checkpoint gives 1.126 (`docs/RESULTS.md`).
- **The released V2X-Traj `ego.ckpt` predates the released code**: it carries
  `interpretable_graph._motion_embed` (1×128), which the model no longer defines, so
  `load_from_checkpoint` fails (`Unexpected key(s) in state_dict`). Dropping the key
  loads it, but it gives 0.96 / 1.70 / 0.20 vs published 0.90 / 1.56 / 0.17. Not a
  valid reproduction; retrain ego on V2X-Traj. The other five checkpoints load strictly.

## RTX 5090 / cu128 images (added 2026-11-16)

GPU 1 is now an RTX 5090 (Blackwell, `sm_120`, 32 GB). What it took to use it:

- **Driver vanished after a reboot.** `unattended-upgrade` installed kernel 7.0.0-43 but
  not `linux-modules-nvidia-580-open-7.0.0-43-generic` (the metapackage upgrade also
  needs the 580.173 → 580.178 userspace upgrade, which it skipped), so the next boot had
  no NVIDIA modules at all and `nvidia-smi` failed for both cards. Fix: `sudo apt install
  linux-modules-nvidia-580-open-generic-hwe-24.04 nvidia-driver-580-open`, reboot. Expect
  it again after future kernel updates. The 50-series needs the *open* modules, ≥ 570.
- **No pre-2.7 torch build runs on it.** `sm_120` kernels first shipped in torch 2.7.0
  with CUDA 12.8. All three original images (1.12.1+cu116, 1.13.1+cu117, 2.0.1+cu118)
  import fine and then fail on the first CUDA op. Hence one extra image per repo:
  `docker/<Name>/Dockerfile.cu128` → compose service `<name>-cu128` (torch 2.7.1+cu128),
  which also runs on the 3090. `setup.sh` copies it next to the normal Dockerfile.
- **`torch.cuda.get_arch_list()` is empty during `docker build`** (no GPU attached), so
  a build-time `assert 'sm_120' in ...` always fails. Assert `torch.version.cuda` in the
  Dockerfile and check the arch list at run time (`verify.sh`).
- **torch ≥ 2.6 defaults `torch.load(weights_only=True)`**, which rejects the pickled
  PyG caches and old Lightning checkpoints. The cu128 images set
  `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` (our own files only).
- **torch ≥ 2.7 needs Python ≥ 3.9** → QCNet's cu128 image moves from 3.8 to 3.10, and
  with it PyG 2.3.0 → 2.6.1 plus `torch_scatter/sparse/cluster` from
  `data.pyg.org/whl/torch-2.7.0+cu128.html` (`--only-binary :all:` so pip can never fall
  back to a source build). The PyG 2.3.0-era `.pkl` caches load unchanged.
- **V2X-Graph on torch 2.x needs two more things.** (1) `nn.TransformerEncoder` now
  passes `is_causal` to every layer; the repo's custom `TemporalEncoderLayer.forward`
  does not accept it → patch `0002-encoder-layer-is-causal-torch2.patch` (harmless on
  torch 1.12, applied for both images). (2) `pytorch_lightning==1.5.2` evaluates fine
  but cannot train: `The provided lr scheduler "<CosineAnnealingLR>" is invalid` (torch
  2.x schedulers derive from `LRScheduler`, not `_LRScheduler`) → 1.9.5 in the cu128
  image only, the last 1.x release, same `Trainer.from_argparse_args` / `gpus=` API.
- **`pkg_resources` again**: `lightning_fabric` 2.0 (QCNet) imports it; a fresh Python
  3.10 env ships setuptools ≥ 81 → `setuptools==69.5.1`.
- **Do not copy upstream's `train.py` loop into a script without
  `torch.multiprocessing.set_sharing_strategy('file_system')`**: with 6+ DataLoader
  workers V2X-Graph hits `unable to open shared memory object ... Too many open files`
  and the run hangs with the GPU memory still allocated.
- **A killed `docker compose run` leaves its container running.** Stopping the shell
  that launched it does not stop the container; check `docker ps` and `docker stop` it.
- **CMP is not ported**: Python 3.7.11, `spconv-cu117`, MTR/OpenCOOD CUDA ops compiled
  with `TORCH_CUDA_ARCH_LIST=8.6`. It stays 3090-only until D1 needs more.
- **Validation of a port = same checkpoint, same data, both images.** See
  `docs/RESULTS.md`, "cu128 port validation". Seeds do not transfer: the same seed gives
  different initial weights/dropout on torch 1.12 and 2.7 (first training loss 8.785 vs
  8.844), so never mix the two images among the seeds of one benchmark row.

## HiVT on V2X-Seq-TFD (added 2026-11-24, checklist B5/C1)

Code: `AIR-THU/DAIR-V2X-Seq` `projects/HiVT_plugin` (the V2X-Seq authors' own baseline);
service `hivt-cu128`, which reuses the `motion-prediction/v2x-graph:cu128` image.

- **No new image.** V2X-Graph is built on HiVT and needs the same stack (torch, PyG 2.6.1,
  PL 1.x, argoverse-api, `dair_map_api`), so a third 13 GB image would be a copy. Build
  `v2x-graph-cu128` first.
- **Same lane-embedding slowdown as V2X-Graph** (it was copied from HiVT): patch
  `0002-hivt-lane-embedding-fast-backward.patch`, generated against the tree after 0001.
- **Same two torch-2 / PyG-2 fixes as V2X-Graph**, in one patch
  (`docker/DAIR-V2X-Seq/patches/0001-hivt-plugin-pyg2-torch2.patch`): the PyG 1.x
  `TemporalData.__inc__` signature, and `TemporalEncoderLayer.forward` without
  `is_causal`. Upstream pins torch 1.8 + PyG 1.7.2.
- **`tools/data_converter/tfd_converter.py` uses `DataFrame.append`**, removed in pandas
  2.0. The cu128 image has pandas 1.4.4, so it runs; do not upgrade pandas there.
- **The cooperative ("online", PP-VIC) input is preprocessing, not learning.**
  `tools/trajectory_fusion/fusion_for_prediction.py` fuses both views into one track per
  object with the same IoU > 0.3 + Hungarian rule that V2X-Graph uses for its labels
  (V2X-Graph's `traj_match_labels/` is a modified copy of this tool); then
  `tfd_converter.py` keeps the fused history and takes the future from the car's own
  tracks. Output: `<root>/cooperative-vehicle-infrastructure/{tfd_fusion,fusion_for_prediction}`.
- **HiVT's own per-scenario processing runs on first use** (`TFDDataset.process`, serial
  loop) and writes `<root>/<split>/processed/*.pt`.
- **Official checkpoints are on Google Drive**, linked from
  `docs/benchmarks/vic-traj-forecasting/README.md` of DAIR-V2X-Seq (no cooperation,
  online, offline). On 2026-11-24 the first `gdown` attempts failed with Drive's "Too many
  users have viewed or downloaded this file recently" quota, like the TFD zips (A1); a
  retry a few hours later worked. They are in `/raid/scratch/hivt_data/checkpoints_official/`.
- **`datasets/tfd_dataset.py` cannot process data as released**: `torch.zeros(..., dtype =
  x.type)` passes a method, not a dtype (fails on any torch) → patch
  `0003-hivt-zeros-dtype.patch` (`x.dtype`). Processing is serial, ~3 scenarios/s
  (TFD val ~1 h, train ~2.2 h).
- **Three different published HiVT numbers on the same val split**: V2X-Seq paper Table 3,
  the DAIR-V2X-Seq README (with checkpoints) and V2X-Graph Table 1 (reportedly a
  re-implementation with hidden size 128; the plugin's default `embed_dim` is 64).
  A fourth one: the V2INet paper (Table 2) retrained HiVT itself: ego 1.34 / 2.16 / 0.31,
  PP-VIC 1.28 / 2.11 / 0.31.
- **`train.py` cannot run the benchmark protocol as released**: it hard-codes
  `seed_everything(2022)`, keeps only the top-5 checkpoints by val minFDE, and never adds the
  Trainer's argparse flags (so no `--accumulate_grad_batches`, no `--default_root_dir`). With
  validation every 5 epochs the final epoch 64 is never saved. Patch
  `0004-hivt-train-seed-accum-save-last.patch` adds `--seed`, `--accumulate_grad_batches`,
  `--default_root_dir`, `--resume_ckpt` and the same `last.ckpt` callback as V2X-Graph 0003.
- **The three official checkpoints were trained with different settings**, readable from
  their stored hyperparameters (`torch.load(ckpt)['hyper_parameters']`): online lr 3e-4,
  2 GPUs × 16; none lr 2.4e-3, 4 GPUs × 64; offline lr 3e-3, 4 GPUs × 80 on the roadside
  view for 10 epochs. The plugin's `train.py` defaults (lr 3e-4, batch 32, 1 GPU) match none
  of them exactly. `docs/RESULTS.md`, "Training configurations".
- **Use `--parallel True` for training.** The default loop over the 50 history steps is
  bound by kernel launches (5090 at ~20 % use, the same time per step at batch 16 or 32).
  The plugin's own `parallel` mode batches the steps into one graph: same outputs (checked
  on the official checkpoint), 2.1× faster on the 5090, 1.4× on the 3090.
- **The fused train set is on the NVMe** too (`/home/baco/nvme_cache/hivt/
  tfd_fused_train_processed`, 37 GB, verified by count, bytes and 300 md5; the HDD original
  is `processed.hdd_backup`); the `hivt-cu128` service mounts `/home/baco/nvme_cache`.

## V2INet on V2X-Seq-TFD (added 2026-11-25, checklist B3)

Code: `xichennn/V2I_trajectory_prediction` (`0b07863`, paper arXiv 2408.00374, v3 Mar 2025);
service `v2inet-cu128`, which also reuses the `motion-prediction/v2x-graph:cu128` image.

- **No new image**: HiVT-based (one HiVT local encoder per view + cross-view attention), same
  stack as the HiVT plugin. The conformal-prediction part (`train_copula.py`) needs `copulae`,
  which the image does not have; not needed for training or the benchmark numbers.
- **No association between views.** `process_argoverse` concatenates the car and roadside
  CSVs; an object seen by both becomes two nodes, marked only by `source` (1 car, 0 roadside).
  Car nodes attend to roadside nodes (cross-view layer); loss and metrics use car nodes only.
  Its time axis is the union of both views' timestamps, which works on TFD because both views
  share the same 10 Hz grid (checked: union = 100 steps in 301 of 301 val scenarios).
- **Four fixes as patches** (`docker/V2I_trajectory_prediction/patches/`, applied by
  `setup.sh`): 0001 `datasets/dair_map_api.py` hard-codes the authors' cluster path
  (`/groups/klhead/...`); the `$DATA_ROOT` line was commented out, restored. 0002
  `V2X.__init__` passes `rotate=` to `CrossViewEncoder`, which has no such argument, so the
  released model cannot be built (`TypeError`). 0003 the same `F.embedding` lane-attribute fix
  as V2X-Graph 0004 / DAIR 0002. 0004 `train.py`: `--seed`, `last.ckpt` callback,
  `--default_root_dir`, `--resume_ckpt`, and it now passes `--check_val_every_n_epoch` (upstream
  parses it but validates every epoch). Note `--accelerator` defaults to `cpu`: pass `gpu`.
- **Layout**: it reads `<root>/<split>/*.csv` (the release's own layout, no `data/` level) and
  writes `<root>/<split>/v2x_processed/` next to the CSVs, so the read-only release needs a
  writable tree: `extras/prepare_tfd_layout.sh` (per-file symlinks for the car view, one
  directory symlink for the roadside view; maps copied from the V2X-Graph staging folder).
  Mounting the repo read-only breaks the nested `/workspace/data_staging` mount.
- **Processing is serial upstream**; `extras/preprocess_parallel.py` calls the same
  `process_argoverse` + `TemporalData` + `torch.save` with 10 workers (~8 scenarios/s on val,
  ~2.3 MB per scenario). Run with `PYTHONHASHSEED=0` (lane order follows a Python `set`).
- **Published configuration differs from the repo defaults**: paper batch 32, lr 1e-3,
  1 cross-view layer; repo batch 4 × accumulation 4, lr 5e-4, `num_global_layers` 3. We use
  the paper's. No checkpoint is released, so our retrain is the reproduction (target
  1.19 / 1.98 / 0.27 on V2X-Seq val, paper Table 2; its V2X-Graph row 1.17 / 2.03 / 0.29 is
  copied from an earlier source and differs from V2X-Graph's own 1.05 / 1.79 / 0.25).
- **Like HiVT, use `--parallel True`**: identical outputs to the loop (checked with the same
  random weights), and the loop runs twice here (two views).

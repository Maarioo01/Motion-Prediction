# CMP / MTR code excerpts for the first-paper proposal

Raw material for building an *accurate* architecture diagram of the proposed change —
paraphrasing alone loses exactly the detail that matters here (the disabled decoder,
the naive slice). Pulled directly from `repos/CMP/MTR/mtr/models_opv2v/
multi_ego_mtr_model.py` and `repos/MTR/mtr/models/` while reading the actual codebase
for [`FIRST_EXPERIMENT_PROPOSAL.md`](FIRST_EXPERIMENT_PROPOSAL.md). Not the full files —
just the parts that show the mechanism.

## 1. CMP wraps plain MTR per-CAV, then aggregates

From `MotionTransformerWithMultiEgoAggregation.forward()` — every CAV in the scene runs
the *same* underlying `MotionTransformer` (imported from `mtr.models_opv2v.model`, the
same architecture as the standalone `repos/MTR` repo) on the whole batched scene, before
any cooperative aggregation happens:

```python
class MotionTransformerWithMultiEgoAggregation(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.model_cfg = config
        self.motion_transformer = MotionTransformer(config)
        # ... self.motion_aggregator = one of 14 variants, picked by config ...

    def forward(self, batch_dict):
        # Batch all CAVs in a scene, then run motion transformer once.
        mtr_outputs, loss, tb_dict, disp_dict = self.motion_transformer(batch_dict)
        mtr_outputs['pre_aggregation_pred_trajs'] = mtr_outputs['pred_trajs'].clone().detach()
        # ... then splits mtr_outputs back out per-CAV using batch_dict['batch_sample_count'] ...
```

For each CAV acting as "ego" in turn, it gathers that CAV's own predictions plus every
*other* CAV's predictions for the same target agents (non-ego CAVs' predicted
trajectories have their first timestep zeroed — `truncated_trajs[:, :, 1:, :] = ...` —
not yet fully understood why; flag as an open question before building on this),
then calls the configured aggregator.

## 2. The config that picks the aggregator (the one actually used for CMP's numbers)

From `repos/CMP/MTR/tools/cfgs/opv2v/opv2v_multiego_cobevt_c256.yaml` (the config behind
the "our cmp" checkpoint referenced throughout `MODELS_OVERVIEW.md`):

```yaml
MOTION_AGGREGATOR:
    NAME: MotionAggregator
    TYPE: 'Transformer' # 'None' or 'MLP' or 'MLPV2' or 'GCN' or 'MOE' or 'MOEV2' or 'Transformer' etc
```

14 total variants exist in the file (`MotionAggregatorMLP`, `MLPV2`, `GCN`, six `MOE*`
variants, `Transformer`, `TransformerV2`) — real evidence of how much the authors
iterated before landing on Transformer.

## 3. The aggregator itself — where the actual bug lives

From `MotionAggregatorTransformer` (the one selected by the config above). This is the
part worth drawing precisely:

```python
class MotionAggregatorTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        self.feature_encoder = MLP(50 * 5, 512)
        self.bev_encoder = nn.Sequential(...)   # BEV features -> 128-d
        self.map_encoder = nn.Linear(49 * 256, 128)
        self.bev_cross_attention = CrossAttention()
        self.map_cross_attention = CrossAttention()

        encoder_layers = TransformerEncoderLayer(768, nhead=8)
        self.transformer_encoder = TransformerEncoder(encoder_layers, num_layers=5)

        # This decoder is defined ... and never called. See forward().
        self.query_embeddings = nn.Parameter(torch.randn(6, 768))
        decoder_layer = nn.TransformerDecoderLayer(d_model=768, nhead=8)
        self.transformer_decoder = nn.TransformerDecoder(decoder_layer, num_layers=5)

        self.trajectory_decoder = MLP(512, 50 * 5)
        self.score_estimator = MLP(6 * 512, 6)

    def forward(self, features_to_aggregate, pred_scores, bev_features, ...):
        # 1. Every contributing CAV's per-mode trajectory embedding for this target
        #    agent is grouped together:
        #    predictions_by_cav[center_object_id] = [embedding_from_cav_1, embedding_from_cav_2, ...]

        # 2. Each embedding is concatenated with THIS aggregating CAV's own BEV + map
        #    context, then passed through 5-layer self-attention:
        enriched_traj_embedding = torch.concat(
            [agent_feature_embeddings, bev_feature_embedding_this_agent, map_feature_embedding_this_agent],
            dim=-1
        )
        agent_feature_embeddings_transformed = self.transformer_encoder(enriched_traj_embedding)

        # 3. THE BUG: reduction to K=6 output modes is a plain slice of the first 6 rows -
        #    order-dependent, not permutation-invariant over the contributing CAVs.
        modes_of_embeddings = agent_feature_embeddings_transformed[:num_modes, :512].contiguous()

        # The line below is the ACTUAL intended reduction — a query-based cross-attention
        # decoder with 6 learnable query tokens, permutation-invariant by construction.
        # It's commented out in the real file:
        # modes_of_embeddings = self.transformer_decoder(self.query_embeddings, agent_feature_embeddings_transformed)

        final_prediction_embeddings.append(modes_of_embeddings)
        scores = self.score_estimator(modes_of_embeddings.view(-1))
```

This is the single most important diagram to get right in the presentation: **encoder
self-attention over concatenated (per-CAV trajectory embedding + this CAV's BEV + this
CAV's map) tokens → [working decoder, disabled] → [naive slice, active] → final K=6
trajectories + scores.** Arm A of the proposal is: swap the last two boxes.

## 4. MTR's core mechanism (what every CAV runs independently, per the paper)

From `repos/MTR/mtr/models/model.py` — the top-level split is literally two modules:

```python
class MotionTransformer(nn.Module):
    def __init__(self, config):
        self.context_encoder = build_context_encoder(self.model_cfg.CONTEXT_ENCODER)
        self.motion_decoder = build_motion_decoder(
            in_channels=self.context_encoder.num_out_channels,
            config=self.model_cfg.MOTION_DECODER
        )

    def forward(self, batch_dict):
        batch_dict = self.context_encoder(batch_dict)   # "global intention localization" input
        batch_dict = self.motion_decoder(batch_dict)     # "local movement refinement"
        ...
```

**Context encoder** (`context_encoder/mtr_encoder.py`): PointNet-style polyline encoders
for agents and map separately, fused via a shared self-attention transformer stack
(either full/global attention or KNN-restricted local attention — `USE_LOCAL_ATTN`
config flag) with sinusoidal positional embeddings for each token's spatial position.

**Motion decoder** (`motion_decoder/mtr_decoder.py`): the "intention points" aren't
learned end-to-end from random init — they're loaded from a **precomputed pickle file**
(`INTENTION_POINTS_FILE`), one fixed set of 2D anchor points per object type, almost
certainly k-means cluster centers of destination endpoints from the training set. A
learnable query embedding attaches to each fixed anchor point; separate cross-attention
decoder stacks (`obj_decoder_layers`, `map_decoder_layers`) refine each query against
both agent tokens and map tokens over multiple decoder layers, producing a GMM output
(regression + classification heads) per mode. An auxiliary "dense future prediction"
head also predicts every *other* agent's own future trajectory as an extra training
signal, not just the target agent's.

## Open question flagged, not yet resolved

The `truncated_trajs[:, :, 1:, :]` zeroing of non-ego CAVs' first predicted timestep
(in `MotionTransformerWithMultiEgoAggregation.forward()`) needs to be understood before
modifying the aggregator — could be a coordinate-frame alignment necessity (each CAV's
raw prediction is in that CAV's own local frame, and this trims the one timestep that
doesn't survive a naive per-agent-centric reference switch), or something else. Trace
this in the actual repo before building on top of it; don't assume from this excerpt
alone.

---
marp: true
theme: default
mermaid: true
paginate: true
title: システムアーキテクチャ
style: |
  .column-container {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: 20px; /* カラム同士の余白を広げる */
  }
  .left-column {
    width: 40%;
    /* 必要なら margin-right や padding を入れて微調整 */
  }
  .right-column {
    width: 60%;
  }
  /* Mermaid 図を左上に寄せて少し縮小する例 */
  .mermaid {
    margin: 0;
    transform: scale(1.1);
    transform-origin: top left;
  }
---

### システムアーキテクチャ
<div class="column-container">
  <div class="left-column">
<div class="mermaid">

```mermaid
%%{init: {'theme': 'neutral', 'flowchart': {'htmlLabels': true}}}%%
graph LR
    A[Main Application]
    subgraph bulletproofs_crate
        BPGen[BulletproofGens]
        RP[RangeProof]
        PG[PedersenGens]
    end
    subgraph curve25519_dalek_ng
        SC[Scalar]
        CR[CompressedRistretto]
    end
    subgraph merlin_crate
        T[Transcript]
    end
    subgraph rand_crate
        OS[OsRng]
    end

    A --> BPGen
    A --> RP
    A --> PG
    A --> T
    A --> OS

    RP --> CR
 ```   
</div> </div>

<div class="right-column">
 
 - **Bulletproofs クレート**: レンジプルーフの生成・検証を担当 
 
 - **curve25519_dalek_ng**: Scalar や RistrettoPoint など、楕円曲線演算を提供 
 - **Merlin**: トランスクリプト管理 - **rand**: 暗号的乱数生成（OsRng） </div> 
 
 </div> 

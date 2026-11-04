# nf-deacon

Runs [Deacon](https://github.com/bede/deacon) host depletion on the simulated reads. Can be used in conjunction with reads produced by
[human-sequence-removal-validation](https://github.com/nfellaby/human-sequence-removal-validation) and summarises read removal across all samples.

## Input

`simulated_samplesheet.csv` (or `.tsv`) with columns `sample,platform,fastq_1,fastq_2`.
`platform` is `illumina` or `ont`; leave `fastq_2` empty for single-end reads.

## Index

In order of precedence:

1. `--deacon_index /path/to/index.idx`: use an existing index
2. `--deacon_reference /path/to/genome.fa.gz`: build one with `deacon index build`
3. Otherwise `--deacon_index_name` (default `panhuman-1`) is fetched once into `--deacon_index_cache`

## Run

```bash
nextflow run . -profile conda \
    --input results/simulated_samplesheet.csv \
    --deacon_index /path/to/panhuman-1.k31w15.idx \
    --outdir depletion_results
```

Filter thresholds go in `ext.args` for `DEACON_FILTER` in `conf/modules.config` (e.g. `-a 1 -r 0`).

## Outputs

- `depletion_summary.tsv`: one row per sample and platform
- `depletion_summary_by_platform.tsv`: totals per platform
- `depletion_summary.html`: self-contained report
- `deacon/<platform>/`: Deacon JSON summaries and retained reads (`--save_filtered_reads false` to skip the reads)
- `pipeline_info/software_versions.yml`

Paired-end counts include both mates. Since every input read is human, retained reads are depletion misses.
# deacon-depletion

Runs [Deacon](https://github.com/bede/deacon) host depletion on the simulated reads produced by
`SYNTH_READS` and summarises read removal across all samples.

## Input

`simulated_samplesheet.csv` (or `.tsv`) with columns `sample,platform,fastq_1,fastq_2`.
`platform` is `illumina` or `ont`; leave `fastq_2` empty for single-end reads.

## Index

In order of precedence:

1. `--deacon_index /path/to/index.idx`: use an existing index
2. `--deacon_reference /path/to/genome.fa.gz`: build one with `deacon index build`
3. Otherwise `--deacon_index_name` (default `panhuman-1`) is fetched once into `--deacon_index_cache`

## Run

```bash
nextflow run . -profile conda \
    --input results/simulated_samplesheet.csv \
    --deacon_index /path/to/panhuman-1.k31w15.idx \
    --outdir depletion_results
```

Filter thresholds go in `ext.args` for `DEACON_FILTER` in `conf/modules.config` (e.g. `-a 1 -r 0`).

## Outputs

- `depletion_summary.tsv`: one row per sample and platform
- `depletion_summary_by_platform.tsv`: totals per platform
- `depletion_summary.html`: self-contained report
- `deacon/<platform>/`: Deacon JSON summaries and retained reads (`--save_filtered_reads false` to skip the reads)
- `pipeline_info/software_versions.yml`

Paired-end counts include both mates. Since every input read is human, retained reads are depletion misses.

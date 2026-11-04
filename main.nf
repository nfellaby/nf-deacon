#!/usr/bin/env nextflow
/*
 * synth-reads: simulate Illumina (DWGSIM) and ONT (PBSIM3) reads from assemblies
 * listed in a samplesheet (sample,fasta[,md5]).
 */
nextflow.enable.dsl = 2

include { DEPLETE_READS } from './subworkflows/deplete_reads'


workflow {

    if (!params.input) {
        error "Please provide a samplesheet with --input"
    }

    def input_ext = params.input.tokenize('.').last().toLowerCase()
    if (!(input_ext in ['csv', 'tsv'])) {
        error "Samplesheet must be .csv or .tsv: ${params.input}"
    }
    def sep = input_ext == 'tsv' ? '\t' : ','

    //
    // Parse samplesheet: sample,platform,fastq_1,fastq_2 (fastq_2 empty for single-end/ONT)
    //
    ch_reads = channel
        .fromPath(params.input, checkIfExists: true)
        .splitCsv(header: true, strip: true, sep: sep)
        .map { row ->
            if (!row.sample || !row.platform || !row.fastq_1) {
                error "Each samplesheet row needs 'sample', 'platform' and 'fastq_1' values: ${row}"
            }
            def platform = row.platform.toLowerCase()
            if (!(platform in ['illumina', 'ont'])) {
                error "Unknown platform '${row.platform}' for ${row.sample}. Use illumina or ont."
            }
            def single_end = !row.fastq_2?.trim()
            def meta = [
                id:         "${row.sample}_${platform}",
                sample:     row.sample,
                platform:   platform,
                single_end: single_end
            ]
            def reads = single_end
                ? [ file(row.fastq_1.trim(), checkIfExists: true) ]
                : [ file(row.fastq_1.trim(), checkIfExists: true), file(row.fastq_2.trim(), checkIfExists: true) ]
            [ meta, reads ]
        }

    DEPLETE_READS ( ch_reads )

    DEPLETE_READS.out.versions
        .collectFile(name: 'software_versions.yml', storeDir: "${params.outdir}/pipeline_info")
}

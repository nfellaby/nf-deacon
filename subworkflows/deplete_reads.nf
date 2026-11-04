#!/usr/bin/env nextflow

include { DEACON_INDEX_FETCH  } from '../modules/local/deacon_indexes'
include { DEACON_INDEX_BUILD  } from '../modules/local/deacon_indexes'
include { DEACON_FILTER       } from '../modules/local/deacon_filter'
include { SUMMARISE_DEPLETION } from '../modules/local/summarise_depletion'

workflow DEPLETE_READS {
    take:
    ch_reads        // [ meta, [ fastq_1, (fastq_2) ] ]

    main:

        ch_versions = channel.empty()

        //
        // Deacon index: existing file > build from FASTA > fetch prebuilt
        //
        if (params.deacon_index) {
            ch_index = channel.value(file(params.deacon_index, checkIfExists: true))
        }
        else if (params.deacon_reference) {
            DEACON_INDEX_BUILD ( channel.value(file(params.deacon_reference, checkIfExists: true)) )
            ch_index    = DEACON_INDEX_BUILD.out.index
            ch_versions = ch_versions.mix(DEACON_INDEX_BUILD.out.versions)
        }
        else {
            DEACON_INDEX_FETCH ( params.deacon_index_name )
            ch_index    = DEACON_INDEX_FETCH.out.index
            ch_versions = ch_versions.mix(DEACON_INDEX_FETCH.out.versions)
        }

        //
        // Deplete reads matching the index
        //
        DEACON_FILTER ( ch_reads, ch_index )
        ch_versions = ch_versions.mix(DEACON_FILTER.out.versions.first())

        //
        // Summary table and HTML report across all samples
        //
        ch_manifest = DEACON_FILTER.out.summary
            .map { meta, json ->
                "${meta.sample}\t${meta.platform}\t${meta.single_end ? 'single' : 'paired'}\t${json.name}"
            }
            .collectFile(name: 'depletion_manifest.tsv', newLine: true, sort: true)

        SUMMARISE_DEPLETION (
            ch_manifest,
            DEACON_FILTER.out.summary.map { _meta, json -> json }.collect()
        )
        ch_versions = ch_versions.mix(SUMMARISE_DEPLETION.out.versions)

    emit:
    reads    = DEACON_FILTER.out.reads
    summary  = SUMMARISE_DEPLETION.out.tsv
    html     = SUMMARISE_DEPLETION.out.html
    versions = ch_versions
}

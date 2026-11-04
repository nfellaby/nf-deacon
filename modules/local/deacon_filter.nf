process DEACON_FILTER {
    tag "$meta.id"
    label 'process_medium'

    container 'community.wave.seqera.io/library/deacon_ca-certificates:6183979d748b6328'

    input:
    tuple val(meta), path(reads)
    path index

    output:
    tuple val(meta), path("${prefix}.deacon*.fastq.gz"), emit: reads
    tuple val(meta), path("${prefix}.deacon.json")     , emit: summary
    path "versions.yml"                                , emit: versions

    script:
    def args    = task.ext.args ?: ''
    prefix      = task.ext.prefix ?: "${meta.id}"
    def outputs = meta.single_end
        ? "-o ${prefix}.deacon.fastq.gz"
        : "-o ${prefix}.deacon_R1.fastq.gz -O ${prefix}.deacon_R2.fastq.gz"
    """
    deacon filter \\
        --deplete \\
        --threads ${task.cpus} \\
        --summary ${prefix}.deacon.json \\
        $args \\
        $index \\
        $reads \\
        $outputs

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        deacon: \$(deacon --version | sed 's/deacon //')
    END_VERSIONS
    """
}

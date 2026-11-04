process DEACON_INDEX_BUILD {
    tag "$fasta"
    label 'process_medium'

    container 'community.wave.seqera.io/library/deacon:0.19.1--895b1fa7c4a50130'

    input:
    path fasta

    output:
    path "${prefix}.idx", emit: index
    path "versions.yml" , emit: versions

    script:
    def args = task.ext.args ?: ''
    prefix   = task.ext.prefix ?: fasta.name.replaceAll(/\.(fa|fasta|fna)(\.gz)?$/, '')
    """
    deacon index build \\
        --threads ${task.cpus} \\
        $args \\
        $fasta \\
        -o ${prefix}.idx

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        deacon: \$(deacon --version | sed 's/deacon //')
    END_VERSIONS
    """
}

process DEACON_INDEX_FETCH {
    tag "$name"
    label 'process_single'

    container 'community.wave.seqera.io/library/deacon:0.19.1--895b1fa7c4a50130'

    input:
    val name

    output:
    path "*.idx"       , emit: index
    path "versions.yml", emit: versions

    script:
    def args = task.ext.args ?: ''
    """
    deacon index fetch $args $name

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        deacon: \$(deacon --version | sed 's/deacon //')
    END_VERSIONS
    """
}
process DEACON_INDEX_BUILD {
    tag "$fasta"
    label 'process_medium'

    container 'community.wave.seqera.io/library/deacon_ca-certificates:6183979d748b6328'

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

    container 'community.wave.seqera.io/library/deacon_ca-certificates:6183979d748b6328'

    input:
    val name

    output:
    path "*.idx"       , emit: index
    path "versions.yml", emit: versions

    script:
    def args = task.ext.args ?: ''
    """
    # rustls needs a CA bundle; conda-built images have no system certificate store
    if [[ -z "\${SSL_CERT_FILE:-}" ]]; then
        for f in "\${CONDA_PREFIX:-/opt/conda}/ssl/cacert.pem" /opt/conda/ssl/cacert.pem; do
            if [[ -s "\$f" ]]; then export SSL_CERT_FILE="\$f"; break; fi
        done
    fi
    
    deacon index fetch $args $name

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        deacon: \$(deacon --version | sed 's/deacon //')
    END_VERSIONS
    """
}
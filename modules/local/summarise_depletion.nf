process SUMMARISE_DEPLETION {
    label 'process_single'

    container 'community.wave.seqera.io/library/python:3.15.2--9307e9470900642f'

    input:
    path manifest
    path summaries, stageAs: 'summaries/*'

    output:
    path "depletion_summary.tsv"            , emit: tsv
    path "depletion_summary_by_platform.tsv", emit: platform_tsv
    path "depletion_summary.html"           , emit: html
    path "versions.yml"                     , emit: versions

    script:
    """
    summarise_depletion.py \\
        --manifest $manifest \\
        --summary-dir summaries \\
        --outprefix depletion_summary

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python3 --version | sed 's/Python //')
    END_VERSIONS
    """
}
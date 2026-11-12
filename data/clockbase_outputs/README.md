# Per-sample ClockBase outputs

The CSV files contain the clock outputs recorded by the released atlas for
the published benchmark series and the expert-annotation series. They are
numerical output tables, without agent transcripts. Their total source size
is 12,848,572 bytes, so no download step is required.

`manifest.json` maps each file to its GEO series, modality, clock columns,
original source path, byte count, and SHA256 hash. Every copied file matches
the hash named in the released atlas. Files retain their original columns
and numerical values, including unavailable outputs as empty cells. The
sample identifier column is `gsm_id` or `GSM`, depending on the source table.
Use the manifest's clock names and the CSV header to choose the output.

Two files can represent a series when different source tables are recorded
by its rows. The filename suffix distinguishes source files; use the
manifest rather than treating the suffix as a version order. No molecular
input matrices are included.

Outputs can contain numerical artifacts. The verification treats clock
outputs with absolute values above 1,000 as missing and applies its sample,
individual, and test requirements before inference. A table's presence does
not make every published record testable. The released predictions in
`reference_results/` already apply the evaluation's eligibility rules.

# Expert group annotation

The expert benchmark compares the calls of an analysis system with calls for
the complete groups defined from sample annotations. This evaluates group
choice and orientation using the same clock outputs and test rules.

`sources.json` lists the series and annotation sources. The prepared source
inventory contains 32 mouse RNA-seq series and 18 human DNA methylation
series. The scored expert reference contains 16 human series, matching the
manuscript. GSE134429 and GSE53841 are prepared but have no scored expert
reference row. Scored subsets can have different coverage after ambiguous
group definitions and unavailable results are excluded.

## Human DNA methylation groups

`human_dnam_groups.jsonl` contains 50 settled group definitions. Each row gives
the source `unit_id`, the name `variant`, GEO series, arm labels, exact field
rules, complete selected GSM lists, and source revision. A rule is an OR over
lists of predicates. Each list is an AND over its predicates, and each
predicate matches a field value exactly. Rules can use `expert` annotation
or public `geo` sample metadata.

`human_dnam_samples.jsonl` contains the public sample fields used by those
rules. It includes every sample in the inventoried GEO series, with `gse`,
`gsm`, a `geo` object, and an `expert` object. An empty expert object means
that ComputAgeBench supplies no annotation for that sample. If a GSM occurs
in multiple source datasets and a field disagrees, that field is null, as in
the original benchmark.

The expert fields derive from ComputAgeBench, revision
`3cf52681537b303a5b7e21df03a3ae0a94ed497e`, dataset DOI
[10.57967/hf/4347](https://doi.org/10.57967/hf/4347). The source dataset card
specifies [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
That license applies to these two derivative files and overrides the
compilation's CC BY 4.0 license for them. The export selects benchmark
series, renames columns, joins public GEO metadata, resolves duplicated
fields, and evaluates the benchmark's frozen group rules.

Attribution: Kriukov D, Efimov E, Kuzmina EA, Khrameeva EE, Dylov DV.
ComputAgeBench: Epigenetic Aging Clocks Benchmark.
[10.1101/2024.06.06.597715](https://doi.org/10.1101/2024.06.06.597715).
The pinned source is available from the
[ComputAgeBench dataset](https://huggingface.co/datasets/computage/computage_bench/tree/3cf52681537b303a5b7e21df03a3ae0a94ed497e).

## Mouse RNA-seq annotation

Tyshkovskiy et al. is a published Nature article:
*Universal transcriptomic hallmarks of mammalian ageing and mortality*,
Nature 654, 173–188 (2026),
[10.1038/s41586-026-10542-3](https://doi.org/10.1038/s41586-026-10542-3).
The source annotation is publicly deposited as
`Data_annotation_absolute_rodents.xlsx` in
[Zenodo record 18763485](https://zenodo.org/records/18763485).

`mouse_rna_groups.jsonl` supplies the benchmark's factual group labels,
field rules, and complete GSM lists derived from this public annotation.
Its schema follows the human group file. The original annotation workbook
and its full sample fields are not redistributed. Obtain that workbook from
the linked deposit to inspect or reconstruct the annotation-based rules.

The cached deposit does not specify a data license for the annotation.
Its description states an MGB Open Access License for the transcriptomic
clock models and package. This repository does not apply that software
license to the data or assert that the underlying annotation is CC BY 4.0.
The source terms remain an open release decision, recorded with each group.

![pipeline](https://github.com/ComparativeGenomicsToolkit/Comparative-Annotation-Toolkit/blob/master/img/cat-logo.png)

This project aims to provide a straightforward end-to-end pipeline that takes as input a HAL-format multiple whole genome alignment as well as a GFF3 file representing annotations on one high quality assembly in the HAL alignment, and produces a output GFF3 annotation on all target genomes chosen.

This pipeline is capable of running both on local cluster hardware as well as on common cloud infrastructure using the [toil](http://toil.readthedocs.io/en/latest/) workflow engine. For full runs on many genomes, a decent amount of computational effort is required. Memory usage is moderate.

![pipeline](https://github.com/ComparativeGenomicsToolkit/Comparative-Annotation-Toolkit/blob/master/img/CAT_pipeline.png)

Above is a flowchart schematic of the functionality of the `CAT` pipeline.

# Installation

The pipeline can be installed by a simple `pip` install: 

`pip install git+https://github.com/ComparativeGenomicsToolkit/Comparative-Annotation-Toolkit.git`

However, at this time, direct pip installation will mean that the `luigi.cfg`, `logging.cfg`, and test files will be buried in your python directory. I am still trying to figure out how to approach this problem. In the meantime, you may be better off instead cloning the directory and installing from your clone:

~~~
git clone git+https://github.com/ComparativeGenomicsToolkit/Comparative-Annotation-Toolkit.git
pip install -e Comparative-Annotation-Toolkit
~~~

If you want to do the direct pip installation, you can grab the config files from the repository and place them in whatever directory you want to execute from, or set the `LUIGI_CONFIG_PATH` environmental variable to point to their location. Or have an ugly log, your choice.

Either form of `pip` installation will install all of the python dependencies. However, there are binary dependencies that must be compiled and installed in addition.

## Dependencies

1. [Kent toolkit](https://github.com/ucscGenomeBrowser/kent). Follow the installation instructions there. Make sure you put the newly created `~/bin/$MACHTYPE` directory on your path.
2. [bedtools](http://bedtools.readthedocs.io/en/latest/).
3. [samtools](http://www.htslib.org/) (1.3 or greater).
4. [Augustus](http://bioinf.uni-greifswald.de/augustus/binaries/). Make sure you are installing `augustus >= 3.3`. You need to follow the instructions to compile `augustus` in comparative augustus mode. This requires that you modify a few lines in the `common.mk` file, and also need to have `sqlite3`, `lp-solve`, `bamtools`, and `libboost` installed. If you are using ubuntu, this should work:
   `apt-get install libboost-all-dev libboost sqlite3 libsqlite3-0 libsqlite3-dev libgsl0-dev lp-solve liblpsolve55-dev bamtools libbamtools-dev`
   
  After you have the primary `augustus` binaries compiled, add the directory to your path. Note that if you move the `augustus` binaries from their original location, you will need to set the `AUGUSTUS_CONFIG_PATH` global variable to point to the species directory. 
  
  You will also need to put the contents of the `scripts` directory on your path. Next, you need to compile the following auxiliary programs from the folder `auxprogs`:
  1. `joingenes`. Compiling this program will place it in the `augustus` binary directory.
  2. `bam2hints`. Compiling this program will place it in the `augustus` binary directory. Requires `bamtools` to be installed. If the `bamtools` headers are not at `/usr/include/bamtools`, you will need to modify the makefile.
  3. `filterBam`. Also requires the `bamtools` headers.
  4. `bam2wig`. Compiling this program will NOT place it in the `augustus` binary directory, you must do so yourself. This program requires you modify the makefile to explicitly point to your installation of `htslib`, `bcftools`, `samtools`, and `tabix`. `Tabix` is now packaged with `htslib`, and both are included in your `kent` directory at `$kent/src/htslib/`.
  5. `homGeneMapping`. This program must also have its makefile at `$augustus/trunks/auxprogs/homGeneMapping/src/Makefile` modified to turn on the `BOOST = true` and `SQLITE = true` flags. Then run `make clean && make` to recompile.
  6. There are a series of perl scripts that you need to place on your path from the `$augustus/trunks/scripts` directory: `wig2hints.pl`, `blat2hints.pl`, `transMap2hints.pl`, and `join_mult_hints.pl`.
5. [HAL toolkit](https://github.com/glennhickey/hal). To install the HAL toolkit, you must also have the [sonLib](https://github.com/benedictpaten/sonLib) repository in the same parent directory. Compile sonLib first, then compile hal. Once hal is compiled, you need to have the binaries on your path. 
6. [wiggletools](https://github.com/Ensembl/WiggleTools). Used to combine RNA-seq expression in assembly hubs.
7. [sambamba](https://github.com/lomereiter/sambamba/releases). Used to name sort faster than samtools for hints building.

In total, you must have all of the binaries and scripts listed below on your path. The pipeline will check for them before executing steps.
`hal2fasta halStats halLiftover faToTwoBit pyfasta gff3ToGenePred genePredToBed genePredToFakePsl bamToPsl blat2hints.pl gff3ToGenePred join_mult_hints.pl pslPosTarget axtChain chainMergeSort pslMap pslRecalcMatch pslMapPostChain augustus transMap2hints.pl joingenes hal2maf gtfToGenePred genePredToGtf bedtools homGeneMapping blat pslCheck pslCDnaFilter clusterGenes pslToBigPsl bedSort bedToBigBed sambamba wig2hints.pl`

# Running the pipeline

This pipeline makes use of [Luigi](https://github.com/spotify/luigi) to link the various steps together. First, start the `luigid` daemon:

`luigid --background --logdir luigi_logs`

Which provides the central scheduler as well as the web UI, which can be accessed at `localhost:8082`. If you don't want to use the daemon, add the flag `--local-scheduler` to the invocation.

To run the test data, change directories to the CAT installation folder and do the following:

`luigi --module cat RunCat --hal=test_data/vertebrates.hal --ref-genome=mm10 --workers=10 --config=test_data/test.config --work-dir test_install --out-dir test_install --local-scheduler --augustus  --augustus-cgp --augustus-pb --assembly-hub > log.txt`

The test should take around 30 minutes to execute. You can track progress in the log file.


# Command line options

As described above, the primary method to executing the pipeline is to follow the invocation `luigi --module cat RunCat --hal=${halfile} --ref-genome=${ref-genome} --config=${config}`. Below are the flags that can modify execution and output.

## Main options

`--hal`: Input HAL alignment file. (REQUIRED).

`--ref-genome`: Reference genome sequence name. Must be present in HAL. (REQUIRED).

`--config`: Path to the config file with annotations and extrinsic hints. See [the config section](#config-file) for more information. (REQUIRED).

`--out-dir`: Output directory. Defaults to `./cat_output`.

`--work-dir`: Working directory. Defaults to `./cat_work`. Stores all the intermediate files as well as the `toil` jobStore. Can be removed after completion (but not if you want to re-do any steps).

`--target-genomes`: List of genomes to use. If not set, all non-reference genomes in the HAL are used. Due to how `luigi` handles command line tuple parameters, this flag must be formatted as if it was a tuple being passed directly to python, single quoted. So, for example, if your target genomes were Human and Mouse, then you would pass `--target-genomes='("Human", "Mouse")'`. As always with python tuples, if you have only one member, you must have a trailing comma.

`--workers`: Number of local cores to use. If running `toil` in singleMachine mode, care must be taken with the balance of this value and the `--maxCores` parameter.

## transMap options
`--global-near-best`: Adjusts the `globalNearBest` parameter passed to `pslCDnaFilter`. Defaults to 0.15. The `globalNearBest` algorithm determines which set of alignments are within a certain distance of the highest scoring alignment for a given source transcript. Making this value smaller will increase the number of alignments filtered out, decreasing the apparent paralogous alignment rate. Alignments which survive this filter are putatively paralogous. 

## AugustusTM(R) options

`--augustus`: Run AugustusTM(R)? 

`--augustus-species`: What Augustus species do we want to use? If your species is not a mammal, please choose [one of the species listed here](http://bioinf.uni-greifswald.de/augustus/).

`--augustus-utr-off`: AugustusTMR will crash trying to predict UTRs if your `--augustus-species` lacks a trained UTR model. You can check if `$augustusDir/config/species/$augustusSecies/$augustusSpecies_utr_probs.pbl` exists. If it does not, set this flag.

## AugustusCGP options

`--augustus-cgp`: Run AugustusCGP?

`--cgp-param`: Parameters file after training CGP on the alignment. See the [AugustusCGP section](#augustuscgp).

`--maf-chunksize`: Size to chunk HAL into. Larger values make the CGP jobs take longer, but reduce problems related to splitting in genic regions. Default is 2500000. If your HAL contains more than 10 or so genomes, reducing this value to 1000000 or so is a good idea to keep job run-times below an hour and avoid going over 8GB of RAM per job. For a 25-way alignment, I set this value to 750000.

`--maf-overlap`: How much overlap to use in HAL chunks. Larger values increase redundant predictions (which are merged). Default is 500000. For a 25-way alignment, I set this value to 150000.

`--cgp-train-num-exons`: Number of exons to require in the alignment subset used for training CGP. See the [AugustusCGP section](#augustuscgp). Default is 5000.

## AugustusPB options

`--augustus-pb`: Run AugustusPB? Will only run on genomes with IsoSeq data in the config file.

`--pb-genome-chunksize`: Size to chunk genome into. Default is 20000000.

`--maf-overlap`: How much overlap to use in genome chunks. Default is 500000.

## Filtering and consensus finding options

`--intron-rnaseq-support`: Amount of RNA-seq intron support a transcript must have to be considered. Must be a value between 0 and 100. Default is 0.

`--exon-rnaseq-support`: Amount of RNA-seq exon support a transcript must have to be considered. Must be a value between 0 and 100. Default is 0.

`--intron-annot-support`: Amount of reference intron annotation support a transcript must have to be considered. Must be a value between 0 and 100. Default is 0.

`--exon-annot-support`: Amount of reference exon annotation support a transcript must have to be considered. Must be a value between 0 and 100. Default is 0.

`--original-intron-support`: Amount of original intron support. See [transcript evaluation](#evaluatetranscripts) description of original introns a transcript must have to be considered. Must be a value between 0 and 100. Default is 0.

`--denovo-num-introns`: For de-novo predictions, discard any transcripts with fewer than these number of introns. Important when RNA-seq data are noisy. Default is 0.

`--denovo-splice-support`: For de-novo predictions, discard any transcripts with less than this percent of RNA-seq intron support. Must be a value between 0 and 100. Default is 0.

`--denovo-exon-support`: For de-novo predictions, discard any transcripts with less than this percent of RNA-seq exon support. Must be a value between 0 and 100. Default is 0.

`--require-pacbio-support`: If set, all isoforms in the final set must be supported by at least one IsoSeq read. This flag is likely to discard a ton of transcripts, so be careful.

`--in-species-rna-support-only`: If set, all of the above intron/exon support flags will look only at RNA-seq/IsoSeq data from the species in question, and not make use of `homGeneMapping` to check support in all species. The output plots will always report in-species support.

`--rebuild-consensus`: A convenience flag to allow you to adjust the flags above. When set, will force the pipeline to re-run consensus finding and will also re-build the downstream plots and assembly hub.

## Assembly hub

`--assembly-hub`: Build an assembly hub? Default is false. Assembly hubs allow you to view your alignments and annotation on the UCSC browser.

`--hub-email`: Optionally, add an email to your assembly hub. Useful if you are planning on publishing the hub.

See below for `toil` options shared with the hints database pipeline.

## Toil

The remaining options are passed directly along to `toil`:

`--batchSystem`: Batch system to use. Defaults to singleMachine. If running in singleMachine mode, no cluster jobs will be submitted. In addition, care must be taken to balance the `--maxCores` field with the `--workers` field with the toil resources in `luigi.cfg`. Basically, you want to make sure that your # of toil resources multiplied by your `--maxCores` is fewer than the total number of system cores you want to use. However, I **highly** recommend using a non-local batch system. See the toil documentation for more.

`--maxCores`: The number of cores each `toil` module will use. If submitting to a batch system, this limits the number of concurrent submissions.


# Config file

The config file contains the paths to two important pieces of information -- the reference GFF3 and the extrinsic hints (bams).

A major component of producing high quality comparative annotations is making use of RNA-seq and/or IsoSeq information. This information is used as hints to the `augustus` gene finding tool along with `transMap`, and is a major component of cleaning up transcript projections. This is also useful if you run the `augustusCGP` or `augustusPB` portions of the pipeline.

If the genetic distances in your alignment are high (say maybe an average identity in the 70s-80s), then you may derive great benefit from using a protein reference, if possible. This will be particularly useful for `augustusCGP`.

A template for the config file is below. At a minimum, your config file must have the annotation section. A example config file is provided in the `test_data` folder.

**BAM files must be indexed!**

~~~~
[ANNOTATION]
Genome = /path/to/reference/gff3

[BAM]
Genome = /path/to/fofn <OR> /path/to/bam1.bam, /path/to/bam2.bam

[INTRONBAM]
Genome = /path/to/fofn/of/noisy/rnaseq

[ISO_SEQ_BAM]
Genome = /path/to/isoseq/bams

[PROTEIN_FASTA]
Genome = /path/to/protein/fasta
~~~~

Note that the BAM/INTRONBAM/ISO_SEQ_BAM fields can be populated either with a comma separated list of BAMs or a single file with a line pointing to each BAM (a FOFN, or file-of-file-names). The reference sequence information will be extracted from the HAL alignment.

For the PROTEIN_FASTA field, every genome you wish to have the protein fasta be aligned to must be on its own separate line. All of these can point to the same FASTA.

## RNA-seq libraries

It is **extremely** important that you use high quality RNA-seq. Libraries should be poly-A selected and paired end with a minimum read length of 75bp. If any of these are not true, it is advisable to place these libraries in the INTRONBAM field. Any genome can have a mix of BAM and INTRONBAM hints.

**BAM files must be indexed!**

## ISoSeq libraries

If you are using IsoSeq data, it is recommended that you doing your mapping with `gmap`. Follow [the tutorial](https://github.com/PacificBiosciences/cDNA_primer/wiki/Aligner-tutorial:-GMAP,-STAR,-BLAT,-and-BLASR).

# GFF3 Reference

CAT relies on a proper GFF3 file from the reference. One very important part of this GFF3 file is the `biotype` tag, which follows the GENCODE/Ensembl convention. The concept of a `protein_coding` biotype is hard baked into the pipeline. Proper division of biotypes is very important for transMap filtering and consensus finding to work properly.

If your GFF3 has duplicate transcript names, the pipeline will complain. One common cause of this is PAR locus genes. You will want to remove PAR genes -- If your GFF3 came from GENCODE, you should be able to do this: `grep -v PAR_Y $gff > $gff.fixed`

# Execution modes

The default mode of this pipeline will perform the following tasks:

1. Lift all annotations present in the input GFF3 to all other genomes in the alignment.
2. Filter these comparative transcripts for paralogous mappings.
3. Evaluate these transcripts for potential problems, assigning a score.
4. Produce a output annotation set as well a series of plots charting how this process went.

These steps will run reasonably fast on one machine without any need for cluster computing. However, to construct a high quality annotation set, it is recommended that the pipeline be run with as many modes of `AUGUSTUS` as possible.

## AugustusTM(R)
The primary parameterization of `AUGUSTUS` for comparative annotation is primarily a method to clean up transMap projections. Due to a combination of assembly error, alignment noise and real biological changes transMap projections have frame shifting indels, missing or incomplete exons, and invalid splice sites. `AugustusTM` is given every protein coding transMap projection one at a time with some flanking sequence and asked to construct a transcript that closely matches the intron-exon structure that `transMap` provides. Since `AUGUSTUS ` enforces a standard gene model, frame shifts and invalid splices will be adjusted to a valid form. In some cases this will mangle the transcript, producing either another isoform or something that does not resemble the source transcript. `AugustusTMR` runs the same genomic interval and transMap derived hints through `AUGUSTUS ` a second time, but with less strict weights on the `transMa`p hints and with the addition of extrinsic hints from RNA-seq and/or IsoSeq. This is particularly useful in regions where an exon was dropped in the Cactus alignment.

`AugustusTM` and `AugustusTMR` can be ran by providing the `--augustus` flag to the pipeline. `AugustusTMR` will only be ran for genomes with extrinsic information in the hints database. If you are running `CAT` on a non-mammal, you will want to modify the `--augustus-species` flag to [one of the species listed here](http://bioinf.uni-greifswald.de/augustus/). Take care to check if your species has a UTR model, and adjust the `--augustus-utr-off` flag accordingly.

## AugustusCGP
`augustusCGP` is the comparative mode of `AUGUSTUS` recently introduced by [Stefanie Nachtweide](https://academic.oup.com/bioinformatics/article/32/22/3388/2525611/Simultaneous-gene-finding-in-multiple-genomes). This mode of `AUGUSTUS` takes as input a HAL format multiple whole genome alignment and simultaneously produces *ab-initio* transcript predictions in all genomes, taking into account conservation as well as any extrinsic information provided. `AugustusCGP` allows for the introduction of novel isoforms and loci in the final gene sets.

`AugustusCGP` can be ran by providing the `--augustus-cgp` flag to the pipeline. If no previously trained model is provided to `AugustusCGP` via the `--cgp-param` flag, then the pipeline will automatically train the model using the given alignment. To do so, random subsets of the alignment will be extracted until `--cgp-train-num-exons` exons are included. In practice, for vertebrate genomes, a few thousand exons corresponding to a few megabases of sequence are sufficient. If your genomes are more dense, this may vary. The trained model will be written to the `AugustusCGP` working directory, and can be used again on alignments with similar genomes.

## AugustusPB
`AugustusPB` is a parameterization of `AUGUSTUS` to try and predict alternative isoforms using long range data. If any IsoSeq data are provided in the config file, and the `--augustus-pb` flag is set, the genomes with IsoSeq data will be run through and the results incorporated in the final gene set. `AugustusPB` runs on single whole genomes.

# Modules

While the primary mode of operation of the pipeline is to launch the `RunCat` module, you may want to run specific modules. Any submodule can be ran by changing the `luigi` invocation to specify a submodule class instead.

## PrepareFiles

This module parses the GFF3 annotation input, creating a genePred format file as well as a sqlite database. In addition, sequence files for all target genomes are extracted and converted to 2bit.

This module will populate the folders `--work-dir/reference` and `--work-dir/genome_files`.

## Chaining

This step is the first precursor step to `transMap`. Pairwise genomic Kent-style chains are produced for each target genome from the designated reference. This step uses `Toil` and can be parallelized on a cluster.

This module will populate the folder `--work-dir/chaining`.

## TransMap

This step runs `transMap`. The chain files are used to project annotations present in the GFF3 from the reference genome to each target genome.

## EvaluateTransMap

This step performs the preliminary classification of `transMap` transcripts. This step populates the `TransMapEvaluation` table in the sqlite database for each target genome with the following classifiers:

1. AlnExtendsOffConfig: Does this alignment run off the end of a contig?
2. AlignmentPartialMap: Did this transcript not map completely?
3. AlnAbutsUnknownBases: Does this alignment have Ns immediately touching any exons?
4. PercentN: Percent of N bases in the alignment.
5. TransMapCoverage.
6. TransMapIdentity.
7. TransMapGoodness: A measure of alignment quality that takes into account both coverage and alignment size in the target. Related to Jim Kent's badness score.
8. TransMapOriginalIntronsPercent: The number of transMap introns within a wiggle distance of a intron in the parent transcript in transcript coordinates.
9. Synteny: Counts the number of genes in linear order that match up to +/- 5 genes.
10. ValidStart -- start with ATG?
11. ValidStop -- valid stop codon (in frame)?
12. ProperOrf -- is the orf a multiple of 3?
   
This module will populate the folder `--work-dir/transMap`.

## FilterTransMap

This module relies on the `globalNearBest` algorithm in `pslCDnaFilter` to resolve paralogies followed by using `clusterGenes` to resolve gene family collapse and overlapping loci.

This process has 4 steps:

1. Filter out all projections whose genomic span is more than 5 times the original transcript. This is a hard coded
filter to deal with the possibility of rearrangements leading to massive transMap projections. This is required also
to allow the minSpan filter in `pslCDnaFilter` to work properly, as `--minSpan` is an effective filter against retroposed
pseudogenes.
2. Run `pslCDnaFilter` using the `globalNearBest` algorithm to identify the best set of alignments. Turning this value
to a smaller number increases the number of alignments filtered out, which decreases the paralogous alignment call rate.
3. Separate coding and non-coding genes and run both through clusterGenes with or without the `-cds` flag.
4. For each gene ID in #2, see if it hits more than one cluster. Pick the highest scoring cluster. This resolves
paralogy to ostensible 1-1 orthologs. This populates the `GeneAlternateLoci` tag.
5. For each cluster ID in #2 that remains after #3, see if it hits more than one gene. If so, then we have a putative
gene family collapse. Pick the highest average scoring gene and discard the other genes, populating the `CollapsedGeneIds`
and `CollapsedGeneNames` tags.
6. Perform a rescue step where transMaps that were filtered out by paralog resolution but overlap a valid cluster
are re-added to the set despite not being `globalNearBest`.

After these steps, the transcripts are evaluated for split genes. This process takes the max span filtered set and
looks at each transcript separately, seeing if there exists projections on either the same contig or different contigs
that are disjoint in original transcript coordinates. This implies that there was a split or a rearrangement.

This module will further populate the folder `--work-dir/transMap`.

## Augustus

As [discussed above](#augustustmr), this module runs `AugustusTM(R)`. If the pipeline is ran without a hints database, only the `AugustusTM` mode will be executed. This process is one of the most computationally intensive steps, and should not be ran without a cluster.

This module will populate the folder `--work-dir/augustus`.

## AugustusCgp

Running `AugustusCGP` is trickier than other modes. If your genomes are not closely related to an existing training set, you may need to perform logistic regression to train `AugustusCGP` before execution. A default parameter set is provided. This mode is also computationally intensive, and requires a cluster.

Each output transcript are assigned a parental gene, if possible. Parental gene assignment is done by looking to see if this transcript has at least 1 exonic base overlap with any [filtered TransMap](##filtertransmap) as well as unfiltered transMap. If the transcript overlaps more than one gene, the [Jaccard metric](http://bedtools.readthedocs.io/en/latest/content/tools/jaccard.html) is used to try and resolve the ambiguity. If no gene stands out, this transcript is discarded. A sqlite table will record both the filtered and unfiltered overlaps.

Transcripts which are not assigned a parental gene will be considered *novel* in the [consensus finding](##consensus) step. Most often, these are the result of gene family expansion or contraction in the reference. Looking at the raw `transMap` track in the final [assembly hub](##assemblyhub) will help resolve this.

This module will populate the folder `--work-dir/augustus_cgp`.

## AugustusPb

Running `AugustusPB` requires that IsoSeq data be provided. This mode runs on single genomes, and attempts to discover new isoforms. Transcripts predicted in this process undergo the same parental gene assignment described above. 

This module will populate the folder `--work-dir/augustus_pb`.

## Hgm

`homGeneMapping` is a companion tool of `AugustusCGP`. This tool uses a HAL alignment to project RNA-seq and annotation information to target genomes. This is used to validate a splice junction in a target genome as being supported in one or more alternative genomes, as well as being supported in the reference annotation. This module populates the `*_Hgm` database table, where `*` is one of `transMap`, `augTM`, `augTMR`, `augCGP` or `augPB` depending on the transcripts being evaluated. This table has the following comma separated columns:

1. AllSpeciesIntronRnaSupport. The number of species with RNA-seq data supporting the intron junctions, in genomic order.
2. AllSpeciesExonRnaSupport. The number of species with RNA-seq data suporting the exons, in genomic order.
3. IntronRnaSupport. Same as #1, but only within this species.
4. ExonRnaSupport. Same as #2, but only within this species.
5. IntronAnnotSupport. A bit vector indicating if the intron junctions are supported by the reference annotation.
6. CdsAnnotSupport. A bit vector indicating if the CDS features are supported by the reference annotation.
7. ExonAnnotSupport. A bit vector indicating if the exon features are supported by the reference annotation.

This module will populate the folder `--work-dir/hgm`.

The output of the `homGeneMapping` module has more information embedded in the output files. Each GTF format file in the above folder has a added column on the end with a string like:

`"0E-6273,1E-1524,2N:M*-1,3E-742,4E-1912,5E-1208"`

Which can be interpreted as 'species 0 had 6273 extrinsic hints (RNA-seq coverage), species 1 has 1524 extrinsic hints, species 2 (the reference) had both a non-coding (N) and coding (M) junction', and so on. The species numeric values are at the top of the file, and correlate to the species ID assigned internally in the hints database. These data can be useful if you want to dig in to a specific annotation.

## AlignTranscripts

Transcript alignment allows for `AugustusTM(R)` transcripts to be compared to their parental `transMap`. As a result, only protein coding transcripts are aligned. For each transcripts, alignment is performed by BLAT two ways -- in frame codon aware alignment, and mRNA alignment. The results of these alignments are saved in the folder `--work-dir/transcript_alignment`. These alignments are used to create functional annotations of transcripts in the [EvaluateTranscripts](#evaluatetranscripts) module. 

## EvaluateTranscripts

A series of classifiers that evaluate transcript pairwise alignments for `transMap` and `AugustusTM(R)` output.

These classifiers are broken down into 2 groups, which will each end up as a table in the database:

\<alnMode\>\_\<txMode\>\_Metrics:

These classifiers are per-transcript evaluations based on both the transcript alignment and the genome context.

1. PercentUnknownBases: % of mRNA bases that are Ns.
2. AlnCoverage: Alignment coverage in transcript space.
3. AlnIdentity: Alignment identity in transcript space.
4. OriginalIntrons. Original introns is a bit vector that evaluates whether the intron junctions in transcript coordinate space are within 5 bases either direction from the original transcript. This is a powerful approach to identifying retroposed pseudogenes or problematic alignments.
5. ValidStart -- start with ATG?
6. ValidStop -- valid stop codon (in frame)?
7. ProperOrf -- is the orf a multiple of 3?
8. AdjStart -- the position of the new thickStart taking frame-shifts into account (genomic coordinates, + strand).
9. AdjStop -- the position of the new thickStop taking frame-shifts into account (genomic coordinates, + strand).

\<alnMode\>\_\<txMode\>\_Evaluation:

These classifiers are per-transcript evaluations based on the transcript alignment.
Unlike the other two tables, this table stores the actual location of the problems (in genome coordinates) as a
BED-like format. In cases where there are multiple problems, they will be additional rows.

1. CodingInsertion: Do we have any frame-shifting coding insertions?
2. CodingDeletion: Do we have any frame-shifting coding deletions?
3. CodingMult3Insertion: Do we have any mod3 coding insertions?
4. CodingMult3Deletion: Do we have any mod3 coding deletions?
5. NonCodingInsertion: Do we have indels in UTR sequence?
6. NonCodingDeletion: Do we have any indels in UTR sequence?
7. InFrameStop: Are there any in-frame stop codons?


Where txMode is one of transMap, augTM, augTMR and alnMode is one of CDS or mRNA.

The evaluation tables will be loaded as tracks in the final [assembly hub](#assemblyhub).

## Consensus

The consensus finding process takes in transcripts from every mode and attempts to find the highest quality ortholog for a source transcript. The de-novo transcript modes are also evaluated for providing novel isoforms or novel loci. The final gene set is output with a series of features measuring how confident the prediction is.

To evaluate `transMap`, `AugustusTM` and `AugustusTMR` transcripts a consensus score is assigned to each. This score is the sum of the alignment goodness, intron/exon annotation support, original intron support, and intron/exon RNA-seq/IsoSeq support if extrinsic data were provided. The transcript with the highest consensus score is chosen.
    
If one of the de-novo `augustus` modes is run, then the those transcripts are evaluated for providing novel information. If a prediction did not overlap any transMap projections, then it is tagged as putative novel and incorporated into the gene set. If a prediction overlaps a `transMap` projection that was filtered out during paralog resolution, then it is tagged as a possible paralog as well as with the names of overlapping transcripts and incorporated into the gene set. If a prediction overlaps a transMap projection and contains a splice junction not seen in the reference annotation, then it is tagged as a novel isoform and incorporated into the gene set as a member of the gene it overlapped with.

After consensus finding is complete, a final filtering process is performed. This filtering process deduplicates the transcript set. Duplicates most often occur when the `augustus` execution modes create an identical transcript model from different input isoforms. In this case, the duplicates are removed and the remaining transcript tagged with the names of alternative source transcripts. Strand resolution throws out transcripts that are on opposite strands. The correct strand is chosen by looking at which contains the most high quality transcripts. Finally, the transcripts are again clustered using `clusterGenes` on CDS intervals to resolve the case where incorporating novel predictions lead to different gene IDs sharing CDS bases.

After consensus finding, a final output gene set is produced in both `GFF3` and `genePred` format. The `genePred` annotations also have a additional `.gp_info` file that has the additional fields described below.

The output will appear in `--output-dir/consensus`.

## Plots

A large range of plots are produced in `--output-dir/plots`. These include:

1. `denovo.pdf`. If either *de-novo* mode was ran, this plot will report the results. See the above description of the tags in [consensus](#consensus) or [GFF3 tags](#gff3-tags) sections.
2. `completeness.pdf`: The number of genes/transcripts successfully mapped over. The top of the x axis is marked with a red line representing the amount of genes/transcripts the source annotation had.
3. `consensus_extrinsic_support`: A violin plot of the level of extrinsic support seen across all species for splices and exons, as found by `homGeneMapping`. Provides a overall plot and a per-biotype plot.
5. `consensus_anotation_support`: A violin plot of the level of annotation support seen across all species for splices and exons, as found by `homGeneMapping`. Provides a overall plot and a per-biotype plot.
6. `coverage.pdf`: A violinplot that shows the overall transcript coverage in the *consensus* set. Provides a overall plot and a per-biotype plot.
7. `identity.pdf`: A violinplot that shows the overall transcript identity in the *consensus* set. Provides a overall plot and a per-biotype plot.
8. `transmap_coverage.pdf`: A violinplot that shows the overall transcript coverage in the filtered transMap output. Provides a overall plot and a per-biotype plot.
9.  `transmap_identity.pdf`: A violinplot that shows the overall transcript identity in the filtered transMap output. Provides a overall plot and a per-biotype plot.
10. `missing_genes_transcripts.pdf`: Similar to `completeness.pdf`, this plot reports the number of genes and transcripts in the original annotation set not found on the target genomes.
11. `paralogy.pdf`: Stacked bar charts of the number of alignments a given source transcript had in each target.
12. `split_genes.pdf`: The number of transMap genes split within and between contigs.
13. `transcript_modes.pdf`: The number of modes that supported a given comparative annotation. Applies only to protein coding transcripts derived from `transMap`, because `AugustusTMR` is not ran on non-coding inputs.
14. `augustus_improvement.pdf`: A scatterplot + density plot reporting the improvement of primary consensus metrics when an `augustus` transcript was chosen over a transMap transcript. The density plot may fail in some cases.
16. `coding_indels.pdf`: The rate of insertions, deletions and indels that are a multiple of 3 are reported from the final consensus set based on the pairwise alignments. Preference is given to the CDS space alignment, if it worked.
17. `IsoSeq_isoform_validation.pdf`: The number of transcripts in the consensus set whose intron structure is exactly validated by at least one IsoSeq read.
18. `gene_family_collapse.pdf`: The X-axis for each plot is the number of genes in the source transcript set that were collapsed into one locus, and the Y-axis is the number of this this occurred. So, for example, if X=1 and Y=200 that means there were 200 instances of 2 genes being collapsed into 1.


### GFF3 tags:

1. `gene_id`: Unique gene ID assigned to this gene.
2. `transcript_id`: Unique transcript ID assigned to this gene.
3. `alignment_id`: Original alignment ID internally used in the pipeline. Provides a link to the gene sets input to consensus finding.
4. `alternative_source_transcripts`: If deduplication collapsed transcripts, report the other `source_transcript` IDs.
5. `exon_annotation_support`: Was this exon supported by the reference annotation?
6. `exon_rna_support`: Was this exon supported by the extrinsic database?
7. `frameshift`: Is this transcript frameshifted relative to `source_transcript`?
8. `gene_biotype`: The `source_gene` biotype. If this is a *de-novo* prediction, this field will say unknown_likely_coding.
9. `intron_annotation_support`: Was this intron supported by the reference annotation?
10. `intron_rna_support`: Was this intron supported by the extrinsic database?
11. `source_gene`: The gene ID of the source gene, if this is a projection transcript.
12. `source_gene_common_name`: The common name of the source gene.
13. `source_transcript`: The ID of the source transcript.
14. `transcript_biotype`: The biotype of the source transcript, or unknown_likely_coding for *de-novo* predictions.
15. `transcript_class`: For projection transcripts, just says ortholog. For *de-novo* transcripts, will be one of poor\_alignment, possible\_paralog, putative\_novel\_isoform, or putative\_novel. See the [consensus finding](#consensus) section for descriptions.
16. `transcript_modes`: Comma separated list of transcript modes. The same information as the transcript_modes.pdf plot.
17. `pacbio_isoform_supported`: Was this isoform supported by at least one IsoSeq read?
18. `paralogy`: Comma separated list of alignments identified as possible paralogs for this transcript.
19. `possible_split_gene_locations`: If this gene was split across multiple contigs, this will have a comma separated list of alternative locations.
20. `collapsed_gene_names`: If this gene was a part of a gene family collapse, this field reports the common names of genes collapsed together here.
21. `collapsed_gene_ids`: Same as above, but with unique identifiers.
22. `gene_alternate_loci`: If this gene was identified to have paralogous mappings that were filtered out, these intervals are where the paralogs were found.

For `GFF3` output, the alignment goodness is in the score field. For `.gp_info`, it is a column. For `.gp_info`, the support features are collapsed into comma separated vectors instead of being on their respective features.



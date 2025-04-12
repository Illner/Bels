# Bels

A Python tool to generate and encode Bayesian networks into CNF formulae.

Supported formats for Bayesian networks: [BIF (Bayesian Interchange Format)](https://www.cs.washington.edu/dm/vfml/appendixes/bif.htm).

**Language**: Python 3.8+ (64-bit)  
**Supported OS**: Linux, macOS (Intel and Apple Silicon), Windows

> [!IMPORTANT]
> The encoder is not optimised for speed.

## Packages

* [pgmpy](https://pypi.org/project/pgmpy/) 0.1.25 (Linux / macOS / Windows)

Install the required package the following:

```bash
pip install --user pgmpy==0.1.25
```

## Bels generator

```console
./Generate.py -h
```

```console
./Generate.py output_file [ -tls positive_integer (min: 2, default: 5) ] 
                          [ -bls positive_integer (min: 2, default: 5) ] 
                          [ -ds positive_integer (min: 2, default: 2) ] 
                          [ -d positive_integer (min: 1, max: 100, default: 100) ] 
                          [ -s positive_integer | None (default: None) ]
```

Files: <br>
&nbsp;&nbsp;&nbsp;&nbsp; **output_file** - name of the output file where the generated BN will be saved (must end with `.bif`)

**-tls** - top layer size *(min: 2, default: 5)* <br>
**-bls** - bottom layer size *(min: 2, default: 5)* <br>
**-ds** - domain size *(min: 2, default: 2)* <br>
**-d** - density *(min: 1, max: 100, default: 100)* <br>
**-s** - seed (ignored for fully dense BNs): if set to None, a new seed will be randomly generated *(default: None)*

## Bels encoder

```console
./Encode.py -h
```

```console
./Encode.py input_file output_file [ -ct {nwDNNF, dDNNF, sdDNNF} (default: nwDNNF) ]
```

Files: <br>
&nbsp;&nbsp;&nbsp;&nbsp; **input_file** - name of the input file (must end with `.bif`) </br>
&nbsp;&nbsp;&nbsp;&nbsp; **output_file** - name of the output file where the CNF formula will be saved

**-ct** - circuit type {nwDNNF, dDNNF, sdDNNF} *(default: nwDNNF)* </br>
&nbsp;&nbsp;&nbsp;&nbsp; `nwDNNF` – negative weak DNNF (nwDNNF) circuit </br>
&nbsp;&nbsp;&nbsp;&nbsp; `dDNNF` – deterministic DNNF (d-DNNF) circuit </br>
&nbsp;&nbsp;&nbsp;&nbsp; `sdDNNF` – smooth deterministic DNNF (sd-DNNF) circuit

## :exclamation: AAAI-25

Bels was used in the following [paper](https://doi.org/10.1609/aaai.v39i14.33643):

    @article{Illner_2025, 
        author  = {Illner, Petr}, 
        title   = {New Compilation Languages Based on Restricted Weak Decomposability}, 
        volume  = {39}, 
        url     = {https://ojs.aaai.org/index.php/AAAI/article/view/33643}, 
        DOI     = {10.1609/aaai.v39i14.33643}, 
        number  = {14}, 
        journal = {Proceedings of the AAAI Conference on Artificial Intelligence}, 
        year    = {2025}, 
        month   = {Apr.}, 
        pages   = {14987-14996} 
    }

### Equally sized top and bottom layers

#### Fully dense

Template: tls_ds_100__... <br>
Example: 4_2_100__n__1

```console
./Generate.py output_file -tls 4 -bls 4 -ds 2 -d 100
```

#### Sparse

Template: tls_ds_d_s__... <br>
Example: 5_2_80_178863288008571802098406570058470324423__d4__1

```console
./Generate.py output_file -tls 5 -bls 5 -ds 2 -d 80 -s 178863288008571802098406570058470324423
```

### Differently sized top and bottom layers

#### Fully dense

Template: tls_bls_ds_100__... <br>
Example: 5_10_2_100__c2d__1

```console
./Generate.py output_file -tls 5 -bls 10 -ds 2 -d 100
```

#### Sparse

Template: tls_bls_ds_d_s__... <br>
Example: 5_10_2_80_215044699595513658902283950224290651799__c__1

```console
./Generate.py output_file -tls 5 -bls 10 -ds 2 -d 80 -s 215044699595513658902283950224290651799
```

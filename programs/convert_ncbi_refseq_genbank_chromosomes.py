#!/usr/bin/env python
"""Convert RefSeq to GenBank or vice versa"""
import argparse
import pandas as pd

header = ['Sequence-Name', 'Sequence-Role', 'Assigned-Molecule', 'Assigned-Molecule-Location/Type',
'GenBank-Accn', 'Relationship', 'RefSeq-Accn', 'Assembly-Unit', 'Sequence-Length', 'UCSC-style-name']


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_gff3', help='RefSeq GFF3 file')
    parser.add_argument('conversion_table', help='Conversion table')
    parser.add_argument('output_gff3', help='Output GFF3')
    parser.add_argument('--refseq-to-genbank', type=bool, default=True, help='Set this to flip direction to RefSeq -> GenBank')
    return parser.parse_args()


if __name__ == "__main__":
    df = pd.read_csv(args.conversion_table, sep='\t', comment='#')
    df.columns = header
    if args.refseq_to_genbank:
        m = dict(zip(df['RefSeq-Accn'], df['GenBank-Accn']))
    else:
        m = dict(zip(df['GenBank-Accn'], df['RefSeq-Accn']))
    with open(args.output_gff3, 'w') as fh:
        for row in open(args.input_gff3):
            if row.startswith('##gff'):
                fh.write(row)
            elif row.startswith('#'):
                continue
            row = row.split('\t')
            if row[0] in m:
                row[0] = m[row[0]]
            else:
                print('Row unparseable: {}'.format(row))
            fh.write('\t'.join(row))
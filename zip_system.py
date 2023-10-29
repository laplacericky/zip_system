#!/usr/bin/env python3
import argparse,sys
import subprocess,os

def path_cannot_exist(path):
    assert not os.path.exists(path), f'{path} exists'


def archiver(obj_name):
    assert os.path.splitext(obj_name)[1] != '.tar'
    output_name = obj_name + '.tar'
    path_cannot_exist(output_name)
    subprocess.run(['tar', 'cf', f'{obj_name}.tar', obj_name], check = True)
    return output_name

def gzip_compressor(filename):
    output_name = filename+'.gz'
    path_cannot_exist(output_name)
    subprocess.run(['gzip', '-v9', filename], check = True)
    return output_name

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices = ['archive','compress','extract'] )
    parser.add_argument('target')
    args = parser.parse_args()
    assert os.path.exists(args.target)
    assert os.path.basename(args.target) == args.target

    if args.mode == 'archive':
        archiver(args.target)

    elif args.mode == 'compress':
        filename = args.target
        if os.path.splitext(filename)[1] != '.tar':
            filename = archiver(filename)
        gzip_compressor(filename)


    elif args.mode == 'extract':
        assert not os.path.isdir(args.target)
        prefix, compression_type = os.path.splitext(args.target)

        match compression_type:
            case '.gz':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                subprocess.run(['gunzip', '-v', args.target], check = True)
            case '.tgz':
                uncompressed_name = prefix + '.tar'
                path_cannot_exist(uncompressed_name)
                subprocess.run(['gunzip', '-v', args.target], check = True)
            case '.tar':
                uncompressed_name = prefix + '.tar'
            case _:
                raise Exception('unsupported compression type')

        prefix, suffix = os.path.splitext(uncompressed_name)

        if suffix == '.tar':
            path_cannot_exist(prefix)
            subprocess.run(['tar', 'xf', uncompressed_name, '--one-top-level'], check = True)
            subprocess.run(['rm', uncompressed_name], check = True)


if __name__ == '__main__':
    assert sys.version_info[0] >= 3 and sys.version_info[1] >= 11
    main()

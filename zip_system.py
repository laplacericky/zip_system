#!/usr/bin/env python3
import argparse,sys
import subprocess,os
import tempfile

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

def bzip2_compressor(filename):
    output_name = filename+'.bz2'
    path_cannot_exist(output_name)
    subprocess.run(['bzip2', '-v9', filename], check = True)
    return output_name

def lzma2_compressor(filename):
    output_name = filename+'.xz'
    path_cannot_exist(output_name)
    subprocess.run(['xz', '-6ev', '-T8', '-M80%', filename], check = True)
    return output_name

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices = ['archive','compress','extract'] )
    parser.add_argument('target')
    parser.add_argument('--compressor', choices = ['deflate','lzma2','bzip2'], default = 'lzma2')
    args = parser.parse_args()
    assert os.path.exists(args.target)
    assert os.path.basename(args.target) == args.target

    match args.compressor:
        case 'deflate':
            compressor = gzip_compressor
        case 'lzma2':
            compressor = lzma2_compressor
        case 'bzip2':
            compressor = bzip2_compressor

    if args.mode == 'archive':
        archiver(args.target)

    elif args.mode == 'compress':
        filename = args.target
        if os.path.splitext(filename)[1] != '.tar':
            filename = archiver(filename)
        compressor(filename)


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
            case '.bz2':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                subprocess.run(['bzip2', '-dv', args.target], check = True)
            case '.xz':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                subprocess.run(['xz', '-dv', '-T8', '-M80%', args.target], check = True)
            case '.zip'|'.7z'|'.rar':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                subprocess.run(['unar', '-d', args.target], check = True)
                contents = os.listdir(uncompressed_name)
                if len(contents) == 1 and os.path.isdir(f'{uncompressed_name}/{uncompressed_name}'):
                    temp_folder = tempfile.mkdtemp(prefix=uncompressed_name, dir='.')
                    subprocess.run(['mv', f'{uncompressed_name}/{uncompressed_name}', temp_folder], check = True)
                    subprocess.run(['rmdir', uncompressed_name], check = True)
                    subprocess.run(['mv', f'{temp_folder}/{uncompressed_name}', '.'], check = True)
                    subprocess.run(['rmdir', temp_folder], check = True)
                subprocess.run(['rm', args.target], check = True)
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

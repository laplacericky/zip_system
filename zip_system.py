#!/usr/bin/env python3
import argparse,sys
import subprocess
import tempfile
from pathlib import Path

def path_cannot_exist(p):
    assert not p.exists(), f'{p} exists'

def append_suffix(p, s):
    return p.with_suffix(p.suffix + s)

def archiver(obj_name):
    assert obj_name.suffix != '.tar'
    output_name = append_suffix(obj_name, '.tar')
    path_cannot_exist(output_name)
    subprocess.run(['tar', 'cf', output_name, obj_name], check = True)
    return output_name

def gzip_compressor(filename):
    output_name = append_suffix(filename, '.gz')
    path_cannot_exist(output_name)
    subprocess.run(['gzip', '-v9', filename], check = True)
    return output_name

def bzip2_compressor(filename):
    output_name = append_suffix(filename, '.bz2')
    path_cannot_exist(output_name)
    subprocess.run(['bzip2', '-v9', filename], check = True)
    return output_name

def lzma2_compressor(filename):
    output_name = append_suffix(filename, '.xz')
    path_cannot_exist(output_name)
    subprocess.run(['xz', '-6ev', '-T8', '-M80%', filename], check = True)
    return output_name

def pre_check(uncompressed_name):
    prefix, suffix = Path(uncompressed_name.stem), uncompressed_name.suffix

    if suffix == '.tar':
        path_cannot_exist(prefix)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices = ['archive','compress','extract'] )
    parser.add_argument('target')
    parser.add_argument('--compressor', choices = ['deflate','lzma2','bzip2'], default = 'lzma2')
    args = parser.parse_args()
    target_path = Path(args.target)
    assert target_path.exists()
    assert target_path.parent == Path('.')

    match args.compressor:
        case 'deflate':
            compressor = gzip_compressor
        case 'lzma2':
            compressor = lzma2_compressor
        case 'bzip2':
            compressor = bzip2_compressor

    if args.mode == 'archive':
        archiver(target_path)

    elif args.mode == 'compress':
        if target_path.suffix != '.tar':
            target_path = archiver(target_path)
        compressor(target_path)


    elif args.mode == 'extract':
        assert not target_path.is_dir()
        prefix, compression_type = Path(target_path.stem), target_path.suffix

        match compression_type:
            case '.gz':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                pre_check(uncompressed_name)
                subprocess.run(['gunzip', '-v', target_path], check = True)
            case '.tgz':
                uncompressed_name = append_suffix(prefix, '.tar')
                path_cannot_exist(uncompressed_name)
                pre_check(uncompressed_name)
                subprocess.run(['gunzip', '-v', target_path], check = True)
            case '.bz2':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                pre_check(uncompressed_name)
                subprocess.run(['bzip2', '-dv', target_path], check = True)
            case '.xz':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                pre_check(uncompressed_name)
                subprocess.run(['xz', '-dv', '-T8', '-M80%', target_path], check = True)
            case '.zip'|'.7z'|'.rar':
                uncompressed_name = prefix
                path_cannot_exist(uncompressed_name)
                pre_check(uncompressed_name)
                subprocess.run(['unar', '-d', target_path], check = True)
                contents = list(uncompressed_name.iterdir())
                repeated_path = uncompressed_name / uncompressed_name
                if len(contents) == 1 and repeated_path.is_dir():
                    temp_folder = Path(tempfile.mkdtemp(prefix=str(uncompressed_name), dir=Path('.')))
                    subprocess.run(['mv', repeated_path, temp_folder], check = True)
                    uncompressed_name.rmdir()
                    subprocess.run(['mv', temp_folder / uncompressed_name, Path('.')], check = True)
                    temp_folder.rmdir()
                target_path.unlink()
            case '.tar':
                uncompressed_name = append_suffix(prefix, '.tar')
            case _:
                raise Exception('unsupported compression type')

        prefix, suffix = Path(uncompressed_name.stem), uncompressed_name.suffix

        if suffix == '.tar':
            path_cannot_exist(prefix)
            subprocess.run(['tar', 'xf', uncompressed_name, '--one-top-level'], check = True)
            uncompressed_name.unlink()


if __name__ == '__main__':
    assert sys.version_info[0] >= 3 and sys.version_info[1] >= 11
    main()

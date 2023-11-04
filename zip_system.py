#!/usr/bin/env python3
import argparse,sys
import subprocess
import tempfile
from pathlib import Path
import shutil

def path_cannot_exist(p):
    assert not p.exists(), f'{p} exists'

def path_must_exist(p):
    assert p.exists(), f'{p} not exists'

def append_suffix(p, s):
    return p.with_suffix(p.suffix + s)

def path_move(p1, p2):
    assert not p1.is_symlink() and not p2.is_symlink()
    assert p1.resolve(strict = True) != p2.resolve()

    if p2.is_dir():
        path_cannot_exist(p2 / p1.name)
    elif p2.is_file():
        raise Exception(f'{p2} exists')

    new_path = shutil.move(p1, p2)
    assert new_path is not None
    return Path(new_path)

def archiver(obj_name):
    assert obj_name.suffix != '.tar'
    output_name = append_suffix(obj_name, '.tar')
    path_cannot_exist(output_name)
    
    #By default, tar archives symlinks as symlinks and will not follow the symlinks
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
    path_must_exist(target_path)
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
                    temp_uncompressed_name = path_move(repeated_path, temp_folder)
                    uncompressed_name.rmdir()
                    path_move(temp_uncompressed_name, Path('.'))
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

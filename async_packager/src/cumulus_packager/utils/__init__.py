"""utilities for the cumulus geoprocessor package
"""

import gzip
import os
import tarfile
import zipfile

from cumulus_packager import logger

this = os.path.basename(__file__)


def file_extension(file: str, preffix: str = "", suffix=".tif", maxsplit=-1):
    """Replace file extension with suffix with allowable extensions

    Parameters
    ----------
    file : str
        input file name or FQPN; don't use preffix with FQPN
    preffix : str, optional
        add preffix to input string, by default ""
    suffix : str, optional
        replace extension with suffix, by default ".tif"
    maxsplit : int, optional
        for multiple ".ext"; e.g. .tar.gz, by default -1

    Returns
    -------
    str
        filename or FQPN with new extension, preffix, or both
    """
    file = preffix + file

    exts = (
        ".gz",
        ".nc",
        ".tar",
        ".bin",
        ".grb",
        ".zip",
        ".bil",
        ".dat",
        ".txt",
        ".tif",
        ".tiff",
        ".grib",
        ".grib2",
        ".tar.gz",
        ".grib.gz",
        ".grib2.gz",
        ".grb.gz",
    )
    if file.endswith(exts):
        file_ = [
            file.replace(file[-len(e) :], suffix) for e in exts if file[-len(e) :] == e
        ]

        # maxsure not to go out of range
        maxsplit = maxsplit - 1 if maxsplit > 0 else maxsplit
        maxsplit = min(len(file_) - 1, maxsplit)

        return file_[maxsplit]

    return file + suffix


def decompress(src: str, dst: str = "/tmp", recursive: bool = False):
    """Decompress gzip, tar, tar gzip, or zip file

    Destination as a temporary directory best used because this methods
    does not clean files/directories

    Parameters
    ----------
    src : str
        input FQPN to compressed file
    dst : str, optional
        FQP to output directory, by default "/tmp"
    recursive : bool, optional
        recursive decompress is gzip, tar, tar gzip, or zip file, by default False

    Returns
    -------
    str
        FQP as a directory or single file if not a tar
    """
    # allowed extensions
    exts = (
        ".gz",
        ".tar",
        ".zip",
        ".tar.gz",
    )

    filename = os.path.basename(src)
    # directory name all gets decompressed too
    if not src.endswith(exts):
        return False

    # try to decompress if compressed
    try:
        with gzip.open(src, "rb") as fh:
            content = fh.read()

            fname = file_extension(filename, suffix="", maxsplit=1)
            src = os.path.join(dst, fname)

            with open(src, "wb") as fp:
                fp.write(content)
    except OSError as ex:
        logger.info(f"Not gzip: {src}")
        logger.info(f"{type(ex).__name__}: {this}: {ex}")

    try:
        if zipfile.is_zipfile(src):
            with zipfile.ZipFile(src) as zip:
                fname = file_extension(filename, suffix="")
                dst_ = os.path.join(dst, fname)
                zip.extractall(dst_)
            return dst_
        elif tarfile.is_tarfile(src):
            with tarfile.open(src) as tar:
                fname = file_extension(filename, suffix="")

                dst_ = os.path.join(dst, fname)

                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, dst_)
                if recursive:
                    for member in tar.getmembers():
                        if member.isfile():
                            decompress(
                                os.path.join(dst_, member.name),
                                dst=dst_,
                                recursive=recursive,
                            )
            return dst_
    except Exception as ex:
        logger.warning(f"{type(ex).__name__}: {this}: {ex}")
        return False

    return src


if __name__ == "__main__":
    pass

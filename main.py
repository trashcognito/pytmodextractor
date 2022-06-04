#!/usr/bin/python3
import sys
import os
import struct
from typing import IO
import zlib
from PIL import Image


def get_string(f: IO):
    length = struct.unpack("B", f.read(1))[0]
    return str(struct.unpack(str(length) + "s", f.read(length))[0], "utf-8")


class FileEntry:
    def __init__(self, start, length, is_compressed):
        self.start = start
        self.length = length
        self.is_compressed = is_compressed

    def get_data(self, f: IO, from_data_offset):
        f.seek(from_data_offset + self.start)
        rawdata = f.read(self.length)
        if self.is_compressed:
            return zlib.decompress(rawdata, -15)
        else:
            return rawdata

    def get_image(self, f: IO, from_data_offset):
        rawdata = self.get_data(f, from_data_offset)
        w = struct.unpack("i", rawdata[4:8])[0]
        h = struct.unpack("i", rawdata[8:12])[0]
        img = Image.frombytes("RGBA", (w, h), rawdata[12:])
        return img

def main():
    if len(sys.argv) == 1:
        print("Usage: ", sys.argv[0], " (filename)")
        sys.exit(-1)
    filepath = sys.argv[1]
    with open(filepath, "rb") as f:
        header = str(struct.unpack("4s", f.read(4))[0], 'utf-8')
        if header != "TMOD":
            print(header)
            print("Invalid Header!")
            sys.exit(-1)
        print("Found Valid Header!")
        loaderversion = get_string(f)
        print("Version: {}".format(loaderversion))
        modhash = f.read(20)
        modsignature = f.read(256)

        _unused = f.read(4)

        modname = get_string(f)
        mod_version = get_string(f)
        filecount = struct.unpack("i", f.read(4))[0]
        print("Mod Name: {}".format(modname))
        print("Mod Version: {}".format(mod_version))
        file_database = dict()
        cur_offset = 0
        for i in range(filecount):
            fpath = os.path.normpath(get_string(f))
            file_size = struct.unpack("i", f.read(4))[0]
            file_start = cur_offset
            file_compressed_len = struct.unpack("i", f.read(4))[0]
            file_obj = FileEntry(file_start, file_compressed_len, file_compressed_len != file_size)
            file_database[fpath] = file_obj
            cur_offset += file_compressed_len
        data_offset = f.tell()

        print("Unpacking...")
        try:
            os.mkdir(modname)
        except FileExistsError:
            pass

        for path, file_obj in file_database.items():

            complete_path = os.path.join(modname, path)
            try:
                os.makedirs(os.path.dirname(complete_path))
            except FileExistsError:
                pass

            if os.path.splitext(complete_path)[1] == ".rawimg":
                image_path = os.path.splitext(complete_path)[0] + ".png"
                img = file_obj.get_image(f, data_offset)
                img.save(image_path)
            else:
                file_data = file_obj.get_data(f, data_offset)
                with open(complete_path, "wb") as newfile:
                    newfile.write(file_data)
        print("Unpacked!")


if __name__ == "__main__":
    main()

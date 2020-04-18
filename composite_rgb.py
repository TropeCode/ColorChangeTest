#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess

info = """Convert single-color layer images to RGB composites.

Given one or more directories, this tool will take layer files
numbered 0-2.png and turn them into an RGB composite with each
color channel representing the respective input image.

If an outline.png is present, this will be included as black in
the output image.

The aforementioned files can also be suffixed with a group name
separated with an underscore (eg. _front, _back). This tool will
create an output image for each group."""

arguments = argparse.ArgumentParser(description=info, formatter_class=argparse.RawTextHelpFormatter)
arguments.add_argument("path", help="directory that contains the input images", nargs="+")
arguments.add_argument("-g", "--gray", help="input images are in grayscale format", action="store_true")
arguments.add_argument("-r", "--recursive", help="include nested directories", action="store_true")
arguments.add_argument("-v", "--verbose", help="show running commands and extra info", action="store_true")

args = arguments.parse_args()

magick_exe = shutil.which("magick")
if not magick_exe:
    print("ImageMagick is not installed.")
    exit(1)

optipng_exe = shutil.which("optipng")
if not optipng_exe:
    print("OptiPNG is not installed. Output will not be optimized.")

path_fail = False
for p in args.path:
    if not os.path.isdir(p):
        print("Directory does not exist: {}".format(p))
        path_fail = True

if path_fail:
    exit(1)

if args.gray:
    print("Using grayscale input format.")

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

#TODO Implement recursive option

for path in args.path:
    print("Scanning path: {}".format(path))
    groups = {}
    with os.scandir(path) as it:
        for entry in it:
            # Assign images to groups
            if entry.is_file() and entry.name.endswith('.png'):
                parts = entry.name[:-4].rsplit("_", 1)
                group = parts[1] if len(parts) == 2 else "main"

                if parts[0].isdigit() or parts[0] == "outline":
                    files = groups.setdefault(group, [])
                    files.append(entry.name)

    for group, files in groups.items():
        print("Converting {} layers...".format(group))

        files.sort()

        outline = None
        if files[-1].startswith("outline"):
            outline = files.pop()

        cs = int((len(files) - 1) / 3)
        for c, chunk in enumerate(chunks(files, 3)):
            cmd = ["magick", "-define", "profile:skip=\"*\"", "-background", "rgba(0,0,0,0)"]

            #FIXME Combine doesn't replicate layered properly (blending becomes additive), need to use composite with tinted layers instead

            # Alpha channel
            if len(chunk) == 3:
                cmd.extend(["(", "(", chunk[0], chunk[1], "-compose", "Over", "-composite", ")", chunk[2], "-composite", ")"])
            elif len(chunk) == 2:
                cmd.extend(["(", chunk[0], chunk[1], "-compose", "Over", "-composite", ")"])
            elif len(chunk) == 1:
                cmd.extend([chunk[0]])

            cmd.extend(["-channel", "A", "-separate", "-write", "mpr:a", "-delete", "0--1"])

            # Layer channels
            src = "R" if args.gray else "A"
            mpr = 0
            if len(chunk) == 3:
                cmd.extend(["(", chunk[0], chunk[1], "-compose", "Dst_Out", "-composite", ")"])
                cmd.extend([chunk[2], "-compose", "Dst_Out", "-composite"])
                if args.gray:
                    cmd.extend(["-alpha", "Remove"])
                cmd.extend(["-channel", src, "-separate", "-write", "mpr:{}".format(mpr), "-delete", "0--1"])
                chunk.pop(0)
                mpr += 1

            if len(chunk) == 2:
                cmd.extend([chunk[0], chunk[1], "-compose", "Dst_Out", "-composite"])
                if args.gray:
                    cmd.extend(["-alpha", "Remove"])
                cmd.extend(["-channel", src, "-separate", "-write", "mpr:{}".format(mpr), "-delete", "0--1"])
                chunk.pop(0)
                mpr += 1

            if len(chunk) == 1:
                cmd.extend([chunk[0]])
                if args.gray:
                    cmd.extend(["-alpha", "Remove"])
                cmd.extend(["-channel", src, "-separate", "-write", "mpr:{}".format(mpr), "-delete", "0--1"])
                chunk.pop(0)
                mpr += 1

            # Combine the channels
            cmd.append("(")
            cmd.extend(["mpr:{}".format(m) for m in range(0, mpr)])
            cmd.extend(["canvas:none" for m in range(mpr, 3)])
            cmd.extend(["mpr:a", "-channel", "RGBA", "-combine"])
            if mpr < 3:
                cmd.extend(["-channel", "RGB"[mpr:], "-evaluate", "set", "0", "+channel"])

            if c == cs and outline:
                # Include outline in last chunk (assumed to be black)
                cmd.extend([outline, "-compose", "Over", "-composite"])

            cmd.append(")")
            cmd.extend(["-strip", "rgb_{}_{}.png".format(c, group)])

            if args.verbose:
                print("Running ({}/{}): {}".format(c + 1, cs + 1, subprocess.list2cmdline(cmd)))

            subprocess.run(cmd, cwd=path)

            if optipng_exe:
                # Optimize output image
                cmd = ["optipng", "--silent", "rgb_{}_{}.png".format(c, group)]
                if args.verbose:
                    print("Running ({}/{}): {}".format(c + 1, cs + 1, subprocess.list2cmdline(cmd)))
                subprocess.run(cmd, cwd=path)

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

def fast_scandir(dirname):
    subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

if args.recursive:
    paths = []
    for path in args.path:
        paths.append(path)
        paths.extend(fast_scandir(path))
    paths.sort()
else:
    paths = args.path

for path in paths:
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
            cmd = ["magick", "-define", "profile:skip=\"*\""]

            cmd.append("(")

            clr = [("R", "GB"), ("G", "RB"), ("B", "RG")]
            for i, img in enumerate(chunk):
                # Isolate each layer to a color channel
                cmd.append("(")
                cmd.extend([img, "-colorspace", "sRGB"])
                cmd.extend(["-channel", clr[i][1], "-evaluate", "Set", "0", "+channel"])
                if not args.gray:
                    cmd.extend(["-channel", clr[i][0], "-evaluate", "Set", "100%", "+channel"])
                cmd.append(")")

            cmd.extend(["-background", "rgba(0,0,0,0)", "-flatten"])

            cmd.append(")")

            if c == cs and outline:
                # Include black outline in last chunk
                cmd.extend(["(", outline, "-channel", "RGB", "-evaluate", "Set", "0", "+channel", ")"])
                cmd.extend(["-compose", "Over", "-composite"])

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

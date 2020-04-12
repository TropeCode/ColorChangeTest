image bg = "#333"

label start:
    scene bg
    show screen hsv_test()
    $ color_picker(new_color)
    return

screen hsv_test():
    fixed:
        fit_first True
        xalign 1.0

        add im.MatrixColor("images/rgb/rgb.png", matrix_recolor_triple(*get_adjusted_colors(base_colors, Color(tuple(new_color)))))

        add "images/lines.png"

define base_colors = (Color("#f39ebd"), Color("#c46e8d"), Color("#fedaee"))

define new_color = [242, 157, 188, 255] # Same as first base color

init python:
    import colorsys
    import math
    import operator

    # Notes: Use imagemagick to combine three layers into one RGBA image

    # convert 0.png 1.png -compose Dst_Out -composite r.png
    # convert r.png 2.png -compose Dst_Out -composite r.png

    # convert 1.png 2.png -compose Dst_Out -composite g.png

    # convert r.png -channel A -separate r.png
    # convert g.png -channel A -separate g.png
    # convert 2.png -channel A -separate b.png

    # convert 0.png 1.png -composite a.png
    # convert a.png 2.png -composite a.png
    # convert a.png -channel A -separate a.png

    # convert r.png g.png b.png -channel RGB -combine rgb.png

    #TODO Simplify intermediate steps (no file output until result)
    # https://www.imagemagick.org/Usage/files/#mpr
    # https://stackoverflow.com/questions/29736137/imagemagick-multiple-operations-in-single-invocation

    def get_adjusted_colors(base_colors, ref_color):
        r = ref_color.hsv
        b = base_colors[0].hsv
        h, s, v = (r[0] - b[0], r[1] / b[1] if b[1] > 0 else 1.0, r[2] - b[2])
        #h, s, v = map(operator.sub, ref_color.hsv, base_colors[0].hsv)
        #h, l, s = map(operator.sub, ref_color.hls, base_colors[0].hls)
        new_colors = []
        for c in base_colors:
            rgb = colorsys.hsv_to_rgb(c.hsv[0] + h, c.hsv[1] * s, c.hsv[2] + v)
            #rgb = colorsys.hls_to_rgb(c.hls[0] + h, c.hls[1] + l, c.hls[2] + s)
            new_colors.append(Color(rgb=rgb))
        return tuple(new_colors)

    def matrix_recolor_triple(color_r, color_g, color_b):
        # Use RGB channels to mix three different colours
        cr = color_r.rgb
        cg = color_g.rgb
        cb = color_b.rgb
        return im.matrix(
            cr[0], cg[0], cb[0], 0, 0,
            cr[1], cg[1], cb[1], 0, 0,
            cr[2], cg[2], cb[2], 0, 0,
            0, 0, 0, 1, 0
        )

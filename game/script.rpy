image bg = "#333"

label start:
    menu:
        "Color picker":
            scene bg
            show screen hsv_test()
            $ color_picker(new_color)
        "RGB test":
            show screen rgb_test()
            pause
    return

screen hsv_test():
    fixed:
        fit_first True
        xalign 1.0

        add im.MatrixColor("images/rgb/rgb_0_main.png", matrix_recolor_rgb(*get_adjusted_colors(base_colors, Color(tuple(new_color)))))

screen rgb_test():
    fixed:
        fit_first True
        xalign 0.0

        add im.MatrixColor("images/blending/0.png", im.matrix.tint(*Color("#f00").rgb)) zoom 0.5
        add im.MatrixColor("images/blending/1.png", im.matrix.tint(*Color("#0f0").rgb)) zoom 0.5
        add im.MatrixColor("images/blending/2.png", im.matrix.tint(*Color("#00f").rgb)) zoom 0.5

        text "Separate layers"

    fixed:
        fit_first True
        xalign 1.0

        add im.MatrixColor("images/blending/rgb_0_main.png", matrix_recolor_rgb(Color("#f00"), Color("#0f0"), Color("#00f"))) zoom 0.5

        text "Composite layers"

define base_colors = (Color("#f39ebd"), Color("#c46e8d"), Color("#fedaee"))

define new_color = [242, 157, 188, 255] # Same as first base color

init python:
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

    def get_adjusted_colors(base_colors, ref_color, v_factors=(1.0, 1.0, 0.7)):
        r = ref_color.hsv
        b = base_colors[0].hsv
        h = r[0] - b[0]
        s = r[1] / b[1] if b[1] > 0 else 1.0
        v = r[2] - b[2] # or: r[2] / b[2] if b[2] > 0 else 1.0
        new_colors = []
        for i, c in enumerate(base_colors):
            new_colors.append(Color(hsv=(
                c.hsv[0] + h,
                c.hsv[1] * s,
                c.hsv[2] + v * v_factors[i] # or: c.hsv[2] * v * v_factors[i] - (1.0 - v_factors[i]) * c.hsv[2]
            )))
        return tuple(new_colors)

    def matrix_recolor_rgb(color_r, color_g, color_b):
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

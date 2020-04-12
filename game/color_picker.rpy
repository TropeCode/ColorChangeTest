default color_history = []
default color_favorites = [[167, 77, 42, 255], [237, 179, 14, 255], [89, 116, 194, 255], [216, 163, 10, 255], [58, 115, 75, 255], [205, 205, 206, 255], [251, 198, 10, 255], [28, 28, 28, 255]]

define interface_color = "gold"

screen color_picker(color, alpha, title, pos_xy, color_default):
    tag color_picker
    zorder 30
    modal True

    # Screen variables
    default rgba = color
    default rgba_old = color
    default hue = 0
    default saturation = 0
    default value = 0
    default _alpha = 0 # Avoid name conflict with 'alpha' screen variable in other active screens
    default edit_mode = False

    # Set HSVA variables based on RGBA when screen shows
    on "show" action Function(color_picker_update_hsva)

    # Colour favourites (Swatches)
    frame:
        area (pos_xy[0], pos_xy[1], 500, 108)
        padding (6, 6)

        text "Colour Swatches" xalign 0.38
        textbutton "Edit":
            xalign 0.8
            text_size 12
            tooltip "Toggle edit mode allowing you to\nremove or add favourite colours"
            action [SelectedIf(edit_mode), ToggleLocalVariable("edit_mode", True, False)]


        if color_history:
            side "c r":
                area (410, 10, 80, 80)

                viewport id "history":
                    draggable False
                    mousewheel True

                    vbox:
                        for c in color_history[::-1]:
                            textbutton rgba_to_hex(c):
                                style "empty"
                                xysize (70, 16)
                                text_size 8
                                text_color "#000"
                                text_hover_color "#fff"
                                text_align (0.5, 0.5)
                                background Solid(tuple(c))
                                action Return(["history", c])

                vbar value YScrollValue("history") xsize 10

        text "History" xpos 418 size 12 yoffset -5
        hbox:
            pos (8, 47)
            spacing 7
            for i in xrange(10):
                frame:
                    style "empty"
                    xysize (32, 33)
                    if i < len(color_favorites):
                        add Frame("interface/color_picker/checker.png", tile=True, ysize=31, xsize=31)
                        if not edit_mode:
                            button:
                                background Solid(tuple(color_favorites[i]))
                                tooltip "Apply this colour"
                                action Return(["use_swatch", color_favorites[i]])
                        else:
                            textbutton "X":
                                xysize (32, 33)
                                background Solid(tuple(color_favorites[i]))
                                text_color "#b20000"
                                text_align (0.5, 0.5)
                                tooltip "Remove from favourites"
                                action Return(["rem_swatch", i])
                    else:
                        if edit_mode:
                            button:
                                style "empty"
                                margin (6, 6, 6, 6)
                                align (0.5, 0.5)
                                background "interface/icons/small/star_yellow.png"
                                tooltip "Add to favourites"
                                action Return(["add_swatch", list(rgba)])


    # Colour picker
    frame:
        area (pos_xy[0], pos_xy[1]+108, 500, 350)
        padding (6, 6)

        text title xalign 0.5 text_align 0.5

        # 2D color map
        frame:
            area (25, 25, 255, 255)
            background Solid(tuple([x * 255 for x in colorsys.hsv_to_rgb(1 - hue, 1, 1)]))
        imagebutton:
            area (25, 25, 255, 255)
            #idle im.MatrixColor(SVGradientImage(size=(255,255)), color_matrix.hue((1- hue) * 360))
            idle Frame("interface/color_picker/saturation_value_gradient.png")
            focus_mask None
            keyboard_focus False
            key_events False
            # Offset is frame position + padding + image position, size is image size
            action Function(color_picker_clicked, offset=(pos_xy[0]+25+6, pos_xy[1]+108+25+6), size=(255, 255))
        draggroup:
            # Allow cursor to extend 8 pixels outside map
            area (25 - 8, 25 - 8, 255 + 16,  255 + 16)
            drag:
                pos (int(saturation * 253), int((1 - value) * 253))
                anchor (0, 0)
                child "interface/color_picker/"+str(interface_color)+"/cursor_sq.png"
                focus_mask None
                activated color_picker_dragged
                dragged color_picker_dragged

        # Hue slider
        vbar:
            area (290, 25, 30, 255)
            value ScreenVariableValue("hue", range=1.0, step=0.01, action=Function(color_picker_update_rgba))
            base_bar hue_gradient_image
            thumb Image("interface/color_picker/"+str(interface_color)+"/cursor_h.png", xalign=0.5)
            thumb_offset 0
            top_gutter 0
            bottom_gutter 0

        if alpha:
            # Alpha slider
            add "interface/color_picker/"+str(interface_color)+"/alpha.png" xpos 22 ypos 287
            add Frame("interface/color_picker/checker.png", tile=True, ysize=30, xsize=255) xpos 25 ypos 290
            bar:
                area (25, 290, 255, 30)
                value ScreenVariableValue("_alpha", range=1.0, step=0.01, action=Function(color_picker_update_rgba))
                base_bar im.MatrixColor(alpha_gradient_image, im.matrix.colorize(rgba, rgba))
                thumb Image("interface/color_picker/"+str(interface_color)+"/cursor_v.png", xalign=0.5)
                thumb_offset 0
                top_gutter 0
                bottom_gutter 0

        # Selected color
        add Frame("interface/color_picker/checker.png", tile=True, ysize=100, xsize=100) xpos 360 ypos 180
        frame:
            area (360, 180, 50, 100)
            background Solid(rgba)
            text "New" xalign 0.5 color "#fff" outlines [(1, "#00000080", 1, 0)]
        frame:
            area (410, 180, 50, 100)
            background Solid(rgba_old)
            text "Old" xalign 0.5 color "#fff" outlines [(1, "#00000080", 1, 0)]

        # Text input
        vbox:
            pos (355, 25)
            spacing 0
            textbutton "Red: " + str(int(rgba[0])):
                size_group "rgba"
                xsize 110
                text_size 12
                clicked Return(["input", 0])
            textbutton "Green: " + str(int(rgba[1])):
                size_group "rgba"
                xsize 110
                text_size 12
                clicked Return(["input", 1])
            textbutton "Blue: " + str(int(rgba[2])):
                size_group "rgba"
                xsize 110
                text_size 12
                clicked Return(["input", 2])
            if alpha:
                textbutton "Alpha: " + str(int(rgba[3])):
                    size_group "rgba"
                    xsize 110
                    text_size 12
                    clicked Return(["input", 3])
            if color_default:
                textbutton "Reset":
                    size_group "rgba"
                    xsize 110
                    text_size 12
                    text_xalign 0.5
                    tooltip "Reset colour to default"
                    clicked Return("reset")

        # Window buttons
        hbox:
            align (1.0, 1.0)
            xoffset -3
            spacing 6
            textbutton "Cancel":
                clicked Return("cancel")
            textbutton "Apply":
                clicked Return(["apply", rgba])

default picking_color = None

define alpha_gradient_image = AlphaGradientImage(size=(255,30))
define hue_gradient_image = HueGradientImage(size=(30,255))

init -1 python:
    import colorsys

    def color_picker(color=[0,0,0,0], alpha=True, title="Pick a colour", pos_xy=(240, 130), color_default=None):
        global picking_color
        picking_color = color # Color object (list) to be updated live
        start_color = list(color) # Keep a copy

        renpy.show_screen("color_picker", tuple(color), alpha, title, pos_xy, color_default)
        while True:
            _return = ui.interact()

            if _return[0] == "input":
                color_picker_input(_return[1])
            elif _return == "reset":
                scope = renpy.get_screen("color_picker").scope
                scope["rgba"] = tuple(color_default)
                color_picker_update_hsva()
                update_picking_color(color_default)
            elif _return[0] == "use_swatch":
                scope = renpy.get_screen("color_picker").scope
                scope["rgba"] = tuple(_return[1])
                color_picker_update_hsva()
                update_picking_color(_return[1])
            elif _return[0] == "add_swatch":
                color_picker_add(_return[1])
            elif _return[0] == "rem_swatch":
                color_picker_rem(_return[1])
            elif _return[0] == "history":
                scope = renpy.get_screen("color_picker").scope
                scope["rgba"] = tuple(_return[1])
                color_picker_update_hsva()
                update_picking_color(_return[1])
            elif _return == "cancel":
                renpy.hide_screen("color_picker")
                update_picking_color(start_color) # Reset live color object
                picking_color = None
                return start_color
            elif _return[0] == "apply":
                renpy.hide_screen("color_picker")
                picking_color = None
                return color # Return live color object instead of _return tuple

    def update_picking_color(rgba):
        global picking_color
        for (i, x) in enumerate(rgba):
            picking_color[i] = x

    def color_picker_input(comp):
        scope = renpy.get_screen("color_picker").scope
        x = renpy.input(["Red", "Green", "Blue", "Alpha"][comp], str(scope["rgba"][comp]), "0123456789", length=3)
        x = max(0, min(255, int(x)))
        tuplist = list(scope["rgba"])
        tuplist[comp] = x
        scope["rgba"] = tuple(tuplist)
        color_picker_update_hsva()
        update_picking_color(scope["rgba"])

    def color_picker_update_hsva():
        scope = renpy.get_screen("color_picker").scope
        (r, g, b, a) = scope["rgba"]
        (h, s, v) = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        scope["hue"] = 1 - h
        scope["saturation"] = s
        scope["value"] = v
        scope["_alpha"] = a / 255.0

    def color_picker_update_rgba():
        scope = renpy.get_screen("color_picker").scope
        (r, g, b) = colorsys.hsv_to_rgb(1 - scope["hue"], scope["saturation"], scope["value"])
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        a = int(scope["_alpha"] * 255)
        scope["rgba"] = (r, g, b, a)
        update_picking_color(scope["rgba"])
        renpy.restart_interaction()

    def color_picker_clicked(offset, size):
        # Mouse screen position to local position
        (x, y) = renpy.get_mouse_pos()
        x = max(0, min(x - offset[0], size[0]))
        y = max(0, min(y - offset[1], size[1]))
        # Update screen variables
        scope = renpy.get_screen("color_picker").scope
        scope["saturation"] = float(x) / size[0]
        scope["value"] = 1 - float(y) / size[1]
        color_picker_update_rgba()
        color_picker_history()

    def color_picker_dragged(drags, drop=None):
        # Compensate for draggable area
        width = drags[0].parent_width - drags[0].w
        height = drags[0].parent_height - drags[0].h
        x = drags[0].x
        y = drags[0].y
        # Update screen variables
        scope = renpy.get_screen("color_picker").scope
        scope["saturation"]  = float(x) / width
        scope["value"] = 1 - float(y) / height
        color_picker_update_rgba()
        color_picker_history()

    def color_picker_history():
        global color_history
        scope = renpy.get_screen("color_picker").scope
        color_history.append(scope["rgba"])
        if len(color_history) > 30:
            del color_history[0]

    def color_picker_add(item):
        global color_favorites
        color_favorites.append(item)

    def color_picker_rem(item):
        global color_favorites
        del color_favorites[item]

    def rgba_to_hex(c):
        return '#%02x%02x%02x%02x' % (c[0], c[1], c[2], c[3])

    class GradientImageBase(im.ImageBase):
        def __init__(self, **properties):
            super(GradientImageBase, self).__init__(**properties)
            self.size = properties.get('size')
            self.cached_surf = None

    class AlphaGradientImage(GradientImageBase):
        def load(self):
            if self.cached_surf != None:
                return self.cached_surf
            # Generate a horizontal alpha gradient
            width = self.size[0]
            surf = renpy.display.pgrender.surface((width, 1), True)
            for x in xrange(width):
                color = (255, 255, 255, x)
                surf.set_at((x, 0), color)
            surf = renpy.display.pgrender.transform_scale(surf, self.size)
            self.cached_surf = surf
            return surf

    class HueGradientImage(GradientImageBase):
        def load(self):
            if self.cached_surf != None:
                return self.cached_surf
            # Generate a vertical hue gradient
            height = self.size[1]
            surf = renpy.display.pgrender.surface((1, height), False)
            for y in xrange(height):
                hue = float(y) / height
                (r, g, b) = colorsys.hsv_to_rgb(hue, 1, 1)
                color = (r * 255, g * 255, b * 255)
                surf.set_at((0, y), color)
            surf = renpy.display.pgrender.transform_scale(surf, self.size)
            self.cached_surf = surf
            return surf

    class SVGradientImage(GradientImageBase):
        def load(self):
            if self.cached_surf != None:
                return self.cached_surf
            # Generate a 2D saturation-value gradient
            (width, height) = self.size
            surf = renpy.display.pgrender.surface(self.size, True)
            for y in xrange(height):
                val = 1 - float(y) / height
                for x in xrange(width):
                    sat = float(x) / width
                    (r, g, b) = colorsys.hsv_to_rgb(0, sat, val)
                    color = (r * 255, g * 255, b * 255)
                    surf.set_at((x, y), color)
            self.cached_surf = surf
            return surf

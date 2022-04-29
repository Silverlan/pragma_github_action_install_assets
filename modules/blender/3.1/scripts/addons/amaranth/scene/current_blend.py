#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""
File Browser > Go to Current Blend's Folder

For when you're lost browsing files and want to go back to the currently
open blend's directory. Look for it on the File Browser's header, only
shows up if the file is saved.
"""

import bpy

# From space_filebrowser.py
def panel_poll_is_upper_region(region):
    # The upper region is left-aligned, the lower is split into it then.
    # Note that after "Flip Regions" it's right-aligned.
    return region.alignment in {'LEFT', 'RIGHT'}


class AMTH_FILE_OT_directory_current_blend(bpy.types.Operator):

    """Go to the directory of the currently open blend file"""
    bl_idname = "file.directory_current_blend"
    bl_label = "Current Blend's Folder"

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir="//")
        return {"FINISHED"}


class FILEBROWSER_PT_amaranth(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Bookmarks"
    bl_label = "Amaranth"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return panel_poll_is_upper_region(context.region)

    def draw(self, context):
      layout = self.layout
      layout.scale_x = 1.3
      layout.scale_y = 1.3

      if bpy.data.filepath:
          row = layout.row()
          flow = row.grid_flow(row_major=False, columns=0, even_columns=False, even_rows=False, align=True)

          subrow = flow.row()
          subsubrow = subrow.row(align=True)
          subsubrow.operator(
              AMTH_FILE_OT_directory_current_blend.bl_idname,
              icon="DESKTOP")


classes = (
    AMTH_FILE_OT_directory_current_blend,
    FILEBROWSER_PT_amaranth
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

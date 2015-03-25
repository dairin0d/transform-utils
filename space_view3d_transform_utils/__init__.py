#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***** END GPL LICENSE BLOCK *****

bl_info = {
    "name": "Batch Transforms (Transform Utils)",
    "description": "Batch Transforms (Transform Utils)",
    "author": "dairin0d, moth3r",
    "version": (0, 4, 0),
    "blender": (2, 7, 0),
    "location": "View3D > Transform category in Tools panel",
    "warning": "Experimental / WIP",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/BatchTransforms",
    "tracker_url": "",
    "category": "3D View"}
#============================================================================#

if "dairin0d" in locals():
    import imp
    imp.reload(dairin0d)
    imp.reload(common)
    imp.reload(coordsystems)
    imp.reload(transform_tools)
    imp.reload(batch_transform)

import bpy

from mathutils import Color, Vector, Euler, Quaternion, Matrix

import time

try:
    import dairin0d
    dairin0d_location = ""
except ImportError:
    dairin0d_location = "."

exec("""
from {0}dairin0d.utils_view3d import SmartView3D
from {0}dairin0d.utils_userinput import KeyMapUtils
from {0}dairin0d.utils_ui import NestedLayout, find_ui_area, ui_context_under_coord
from {0}dairin0d.bpy_inspect import prop, BlRna
from {0}dairin0d.utils_addon import AddonManager
""".format(dairin0d_location))

from . import common
from . import coordsystems
from . import transform_tools
from . import batch_transform

addon = AddonManager()

#============================================================================#

"""
PROBLEMS:
* the way I work with axis-angle rotation mode seems buggy
* unlimited workplane causes "View All" operator to "corrupt" 3D view. Right now I block the shortcut, but it might be better to provide a custom override
* bug/glitch with VIEW system, noticeable when chosed as a manipulator orientation (view matrix (or other params) lag one frame behind, which leads to visible distortions of the manipulator when rotating the view)

\\ vmath / gmath for various vector/geometric utilities?

\\ Alt+Numpad shortcuts seem to be not occupied by anything, so I can probably use them for Align View To Workplane.

Transform Tools:
    * is it possible to rotate around workplane using numpad keys?
        * provide custom implementation of "Numpad navigation" (and "View All")
    
    * Spatial tools (snap/align cursor/workplane/coordsystem/selection)
        * option: snap/align selection as a whole or each element individually
        * ability to align workplane to object / polygon / plane
        * "axis-matching rotation" operator (rotate selection to make one vector parallel to another)
        * add operation to align object to workplane via its face
            think of an operation to "unrotate" an object which has rotated data
            \\ as an example (though probably not optimal):
            http://blenderartists.org/forum/showthread.php?256295-Script-to-align-objects-to-a-face-and-line-on-that-face
        
        * Workplane from world/view/object/orientation/coordsystem XY/YZ/XZ
        * Workplane from selection (orthogonal to normal)
        * Workplane from 3D-view-picked normal
        * Workplane from 3 selected objects/elements (will lie in the plane)
        * Workplane from 2 selected objects/elements (will be orthogonal to line)
    
    * Spatial queries? ("select all objects wich satisfy the following conditions")
        * Distance to point/curve/surface/volume
        * Dot product/angle to vector
        * Intersection (as point/wire/surface/volume) with point/curve/surface/volume
        * Raycast?
        * option: how to store the result: as selection or as object/vertex group
    
    * Move/rotate/scale workplane and/or cursor
        * switch absolute/relative coords (mostly useful for snapping to grid/increments, as it defines the grid origin)
        * switch coordinate systems
        * switch move/rotate/scale modes
        * axis locks
        * header display of modes/coordinates
            * customizable precision
        * snap to bbox/faces/edges/vertices/grid
        * snap to raw/preview/render mesh
        * flat or interpolated normal
        * option to snap only to solid?
        * snap cursor to workplane's plane (if it's visible)
        * option to adjust cursor and view when picking workplane? (also: adjust workplane and view when picking cursor position)
    
    * stick cursor/workplane to object/bone/polygon (stored in scene?)
    * cursor history (show trace, max size, current entry)
    * cursor hiding
    * options to draw guides and snap elements (?)
    
    * CAD-like guides?
    
    * copy/paste to workplane? (moth3r's idea, not really sure what he meant)

Copy/Paste coordinates:
    * customizable decimal and axis separators for coordinate copy-pasting (e.g. dot/comma, comma/semicolon/space/tab/newline)
    * Summary extras: per-vector copy/paste (respecting uniformity locks) (option: using units or the raw values ?)
    * Vector extras: swizzle? (evaluate as python expression? e.g. w,x,y,z -> -w,0.5*z,y,2*x) (option: apply to summary or to each individual object)
    * Vector extras: per-summary copy/paste (respecting uniformity locks) (option: using units or the raw values ?)
        * \\ cursor/bookmark/etc. to active/min/max/center/mean/median? (redundant: can be achieved via copy-pasting, given that coordinate system is the same)

"Particle Ensemble transformation"? (representing each individual vertex as a particle object with full matrix might be not very efficient)

For EDIT_ARMATURE mode: implement aggregation of other settings from EditBone?
    use_deform
    use_envelope_multiply
    bbone_segments
    bbone_in
    bbone_out

* sync coordsystems/summaries/etc. between 3D views
* Pick transform? (respecting axis locks)
* Grase pencil summaries?

see also: http://modo.docs.thefoundry.co.uk/modo/601/help/pages/modotoolbox/ActionCenters.html

See Modo's Absolute Scaling
https://www.youtube.com/watch?v=79BAHXLX9JQ
http://community.thefoundry.co.uk/discussion/topic.aspx?f=33&t=34229
see scale_in_modo.mov for ideas
fusion 360 has a lot of cool features (moth3r says it's the most user-friendly CAD)

\\ Ivan suggests to check the booleans addon (to test for possible conflicts)
\\ Ivan suggests to report blender bugs

documentation (Ivan suggests to use his taser model for illustrations)
(what's working, what's not)
(no need to explain what's not working)
(Ivan suggests to post on forum after he makes video tutorial)
"""

@addon.Preferences.Include
class ThisAddonPreferences:
    use_panel_left = True | prop("Show in T-panel", name="T (left panel)")
    use_panel_right = False | prop("Show in N-panel", name="N (right panel)")
    epsilon = 1e-6 | prop("Number equality threshold", name="Epsilon", min=0.0, max=1.0, step=1, precision=8)
    
    gridcolors = batch_transform.GridColorsPG | prop()
    gridstep_small = 5 | prop(min=1, max=100)
    gridstep_big = 1 | prop(min=1, max=100)
    
    workplane_color = Color((0.25, 0.35, 0.5)) | prop(alpha=0.25)
    workplane_lines_color = Color((1, 1, 1)) | prop(alpha=0.5)
    workplane_lines10_color = Color((1, 1, 1)) | prop(alpha=1.0)
    workplane_stipple = 2 | prop(min=1, max=256)
    
    auto_align_objects = True | prop("Automatically switch between World and View alignment of new objects")
    
    def draw(self, context):
        layout = NestedLayout(self.layout)
        
        with layout.row()(alignment='LEFT'):
            layout.prop(self, "use_panel_left")
            layout.prop(self, "use_panel_right")
            with layout.row():#(alignment='EXPAND'):
                layout.prop(self, "epsilon", text="Tolerance ")
        
        with layout.row()(alignment='LEFT'):
            layout.prop(self, "gridstep_small", text="Grid step (small)")
            layout.prop(self, "gridstep_big", text="Grid step (big)")
        
        with layout.row()(alignment='LEFT'):
            layout.prop(self.gridcolors, "x", text="X")
            layout.prop(self.gridcolors, "y", text="Y")
            layout.prop(self.gridcolors, "z", text="Z")
            layout.prop(self.gridcolors, "xy", text="XY")
            layout.prop(self.gridcolors, "xz", text="XZ")
            layout.prop(self.gridcolors, "yz", text="YZ")
        
        with layout.row()(alignment='LEFT'):
            layout.prop(self, "workplane_color", text="Workplane")
            layout.prop(self, "workplane_lines_color", text="Lines")
            layout.prop(self, "workplane_lines10_color", text="Lines-10")
            layout.prop(self, "workplane_stipple", text="Stipple")
        
        with layout.row()(alignment='LEFT'):
            layout.prop(self, "auto_align_objects", text="Auto switch 'Editing\Align To'")

def register():
    addon.use_zbuffer = True
    addon.register()

def unregister():
    addon.unregister()

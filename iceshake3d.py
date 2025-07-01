bl_info = {
    "name": "Import TXT Dummy",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "File > Import",
    "description": "Import a TXT file and print its contents to the console.",
    "category": "Import-Export",
}


import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

class ImportTxtDummy(Operator, ImportHelper):
    bl_idname = "import_test.txt_dummy"
    bl_label = "Import TXT Dummy"
    filename_ext = ".txt"

    filter_glob: bpy.props.StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        print("ImportTxtDummy operator called.")  # <--- Print when import is executed
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            print("TXT FILE CONTENTS:")
            print(content)
            self.report({'INFO'}, "File loaded, check the system console.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load file: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportTxtDummy.bl_idname, text="Import TXT Dummy (.txt)")

def register():
    print("[Import TXT Dummy] Add-on enabled!")  # <--- Print when add-on is enabled
    bpy.utils.register_class(ImportTxtDummy)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    print("[Import TXT Dummy] Add-on disabled!")  # <--- Print when add-on is disabled
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ImportTxtDummy)

if __name__ == "__main__":
    register()

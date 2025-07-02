bl_info = {
    "name": "Import MS3D Dummy",
    "author": "Ramon Wong",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "File > Import",
    "description": "Import a MilkShape3D (MS3D) file and print header info.",
    "category": "Import-Export",
}


import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
import struct


class ImportMS3DDummy(Operator, ImportHelper):
    bl_idname = "import_test.ms3d_dummy"
    bl_label = "Import MS3D Dummy"
    filename_ext = ".ms3d"

    filter_glob: bpy.props.StringProperty(
        default="*.ms3d",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        print("ImportMS3DDummy operator called.")
        try:
            with open(self.filepath, 'rb') as f:
                header_data = f.read(14)
                id_str, version = struct.unpack('<10sI', header_data)
                id_str = id_str.decode('ascii').rstrip('\0')
                print(f"MS3D Header: {id_str}")
                print(f"MS3D Version: {version}")
                self.report({'INFO'}, f"Header: {id_str}, Version: {version}")

                ### Read number of vertices

                num_vertices = struct.unpack('<H', f.read(2))[0]
                print(f"Num Vertices: {num_vertices}")

                # Read each vertex
                for i in range(num_vertices):
                    data = f.read(15)
                    flags, x, y, z, bone_id, ref_count = struct.unpack('<BfffbB', data)
                    # print(f"Vertex {i}: ({x}, {y}, {z}) Bone ID: {bone_id} Flags: {flags} RefCount: {ref_count}")

                ### End of Reading the vertices
                ###
                ### Read number of triangles (unsigned short)

                num_triangles = struct.unpack('<H', f.read(2))[0]
                print(f"Num Triangles: {num_triangles}")

                # Triangle struct is 70 bytes
                for i in range(num_triangles):
                    data                    = f.read(70)
                    unpacked                = struct.unpack('<H3H9f3f3fBB', data)

                    flags                   = unpacked[0]
                    vIndices                = unpacked[1:4]
                    vertex_normals          = unpacked[4:13]    # 9 floats
                    s                       = unpacked[13:16]   # 3 floats
                    t                       = unpacked[16:19]   # 3 floats
                    smoothing_group         = unpacked[19]
                    group_index             = unpacked[20]
                    # print(f"Triangle {i}: vIndices={vIndices} SmoothingGroup={smoothing_group} GroupIndex={group_index}")
                    # Optionally print more data if needed

                ### End of Reading the triangles
                ### Read number of meshes (unsigned short)

                num_meshes = struct.unpack('<H', f.read(2))[0]
                print(f"Num Meshes: {num_meshes}")

                for mesh_i in range(num_meshes):
                    # Fixed-size mesh header
                    mesh_header = f.read(35)
                    flags, name, num_tris = struct.unpack('<B32sH', mesh_header)
                    name = name.decode('ascii', errors='ignore').rstrip('\0')

                    # Variable-size triangle indices
                    tris_indices = [struct.unpack('<H', f.read(2))[0] for _ in range(num_tris)]

                    # Material index (signed char)
                    material_index = struct.unpack('<b', f.read(1))[0]

                    print(f"Mesh {mesh_i}: Name='{name}', NumTriangles={num_tris}, MaterialIndex={material_index}, Flags={flags} ")

                ### End of Reading the vertices
                ###
                ### Read number of materials (unsigned short)

                num_materials = struct.unpack('<H', f.read(2))[0]
                print(f"Num Materials: {num_materials}")

                for mat_i in range(num_materials):
                    data = f.read(361)
                    unpacked = struct.unpack('<32s4f4f4f4fffb128s128s', data)
                    name = unpacked[0].decode('ascii', errors='ignore').rstrip('\0')
                    ambient = unpacked[1:5]
                    diffuse = unpacked[5:9]
                    specular = unpacked[9:13]
                    emissive = unpacked[13:17]
                    transparency = unpacked[17]
                    shininess = unpacked[18]
                    mode = unpacked[19]
                    # texture = unpacked[20].decode('ascii', errors='ignore').rstrip('\0')
                    # alpha_map = unpacked[21].decode('ascii', errors='ignore').rstrip('\0')
                    texture = extract_cstring(unpacked[20])
                    alpha_map = extract_cstring(unpacked[21])
                    print(f"Name='{name}'")
                    print(f"Texture='{texture}'")
                    print(f"Alphamap='{alpha_map}'")
                    print(f"Material {mat_i}: Name='{name}', Ambient={ambient}, Diffuse={diffuse}, Specular={specular}, Emissive={emissive}")



        except Exception as e:
            self.report({'ERROR'}, f"Failed to load MS3D file: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

def extract_cstring(raw_bytes):
    return raw_bytes.partition(b'\0')[0].decode('ascii', errors='ignore').strip()

def menu_func_import(self, context):
    self.layout.operator(ImportMS3DDummy.bl_idname, text="Import MS3D Dummy (.ms3d)")


def register():
    bpy.utils.register_class(ImportMS3DDummy)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    print("[Import MS3D Dummy] Add-on enabled!")


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ImportMS3DDummy)
    print("[Import MS3D Dummy] Add-on disabled!")



if __name__ == "__main__":
    register()

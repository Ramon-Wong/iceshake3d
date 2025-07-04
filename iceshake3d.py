bl_info = {
    "name": "Import MS3D Dummy",
    "author": "Ramon Wong",
    "version": (2, 0),
    "blender": (2, 90, 0),
    "location": "File > Import",
    "description": "Import a MilkShape3D (MS3D) file and print header info.",
    "category": "Import-Export",
}


import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
import struct
import math
import os



def extract_cstring(raw_bytes):
    return raw_bytes.partition(b'\0')[0].decode('ascii', errors='ignore').strip()

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

        # Local lists to hold parsed data
        vertices    = []
        triangles   = []
        meshes      = []
        materials   = []

        try:
            with open(self.filepath, 'rb') as f:
                header_data = f.read(14)
                id_str, version = struct.unpack('<10sI', header_data)
                id_str = id_str.decode('ascii').rstrip('\0')
                print(f"MS3D Header: {id_str}")
                print(f"MS3D Version: {version}")
                self.report({'INFO'}, f"Header: {id_str}, Version: {version}")

                # --- Vertices ---
                num_vertices = struct.unpack('<H', f.read(2))[0]
                print(f"Num Vertices: {num_vertices}")

                for i in range(num_vertices):
                    data = f.read(15)
                    flags, x, y, z, bone_id, ref_count = struct.unpack('<BfffbB', data)
                    vertex = {
                        "flags": flags,
                        "co": (x, y, z),
                        "bone_id": bone_id,
                        "ref_count": ref_count,
                    }
                    vertices.append(vertex)

                # --- Triangles ---
                num_triangles = struct.unpack('<H', f.read(2))[0]
                print(f"Num Triangles: {num_triangles}")

                for i in range(num_triangles):
                    data = f.read(70)
                    unpacked = struct.unpack('<H3H9f3f3fBB', data)
                    flags = unpacked[0]
                    v_indices = unpacked[1:4]
                    normals = [tuple(unpacked[4+j*3:4+(j+1)*3]) for j in range(3)]
                    s = unpacked[13:16]
                    t = unpacked[16:19]
                    smoothing_group = unpacked[19]
                    group_index = unpacked[20]
                    triangle = {
                        "flags": flags,
                        "indices": v_indices,
                        "normals": normals,
                        "s": s,
                        "t": t,
                        "smoothing_group": smoothing_group,
                        "group_index": group_index,
                    }
                    triangles.append(triangle)

                # --- Meshes ---
                num_meshes = struct.unpack('<H', f.read(2))[0]
                print(f"Num Meshes: {num_meshes}")

                for mesh_i in range(num_meshes):
                    mesh_header = f.read(35)
                    flags, name, num_tris = struct.unpack('<B32sH', mesh_header)
                    name = name.decode('ascii', errors='ignore').rstrip('\0')
                    tris_indices = [struct.unpack('<H', f.read(2))[0] for _ in range(num_tris)]
                    material_index = struct.unpack('<b', f.read(1))[0]
                    mesh = {
                        "flags": flags,
                        "name": name,
                        "triangle_indices": tris_indices,
                        "material_index": material_index,
                    }
                    meshes.append(mesh)

                # --- Materials ---
                num_materials = struct.unpack('<H', f.read(2))[0]
                print(f"Num Materials: {num_materials}")

                for mat_i in range(num_materials):
                    data = f.read(361)
                    unpacked = struct.unpack('<32s4f4f4f4fffb128s128s', data)
                    name = extract_cstring(unpacked[0])
                    ambient = unpacked[1:5]
                    diffuse = unpacked[5:9]
                    specular = unpacked[9:13]
                    emissive = unpacked[13:17]
                    shininess = unpacked[17]
                    transparency = unpacked[18]
                    mode = unpacked[19]
                    texture = clean_ms3d_path(extract_cstring(unpacked[20]))
                    alpha_map = clean_ms3d_path(extract_cstring(unpacked[21]))
                    material = {
                        "name": name,
                        "ambient": ambient,
                        "diffuse": diffuse,
                        "specular": specular,
                        "emissive": emissive,
                        "shininess": shininess,
                        "transparency": transparency,
                        "mode": mode,
                        "texture": texture,
                        "alpha_map": alpha_map,
                    }
                    materials.append(material)

                # Notify successful parse
                print(f"Parsed {len(vertices)} vertices, {len(triangles)} triangles, {len(meshes)} meshes, {len(materials)} materials.")
                for imat, mat in enumerate(materials):
                    texture_path    = mat['texture']
                    alpha_map       = mat['alpha_map']

                    if texture_path:
                        abs_path = os.path.join(os.path.dirname(self.filepath), texture_path)
                        if os.path.exists(abs_path):
                            print(f"Material {imat}: Texture Path = '{texture_path}' found")
                        else:
                            print(f"Texture path NOT found: {abs_path}")


                    if alpha_map:
                        abs_path = os.path.join(os.path.dirname(self.filepath), alpha_map)
                        if os.path.exists(abs_path):
                            print(f"Material {imat}: Texture Path = '{texture_path}' found")
                        else:
                            print(f"Texture path NOT found: {abs_path}")


                self.report({'INFO'}, f"Parsed {len(vertices)} vertices, {len(triangles)} triangles, {len(meshes)} meshes, {len(materials)} materials.")


                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.object.delete(use_global=False)

                vertex_coords   = [v['co'] for v in vertices]
                triangle        = [t['indices'] for t in triangles]

                mesh            = bpy.data.meshes.new("MS3D_Mesh")
                obj             = bpy.data.objects.new("MS3D_Object", mesh)
                obj.rotation_euler[0] = math.radians(90)
                context.collection.objects.link(obj)
                mesh.from_pydata(vertex_coords, [], triangle)
                mesh.update()

                # --- Insert normals here ---
                split_normals   = []
                for tr in triangles:
                    # 1. Build the split normals:
                    split_normals.extend( tr['normals'])

                    # 2. Enable auto smooth
                    mesh.use_auto_smooth = True
                    mesh.calc_normals_split()  # Prepares the mesh for custom split normals
                    mesh.normals_split_custom_set(split_normals)
                    mesh.update()

                # --- End normals         ---


                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)



                # You now have the raw arrays: vertices, triangles, meshes, materials
                # You can use these for further mesh/material creation in Blender.

        except Exception as e:
            self.report({'ERROR'}, f"Failed to load MS3D file: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

def clean_ms3d_path(path):
    # Replace backslashes with forward slashes, remove leading './', '.\', or '\'
    path = path.replace('\\', '/')
    path = path.lstrip('./\\')
    return path

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

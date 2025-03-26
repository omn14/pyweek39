from direct.showbase.ShowBase import ShowBase
from panda3d.core import FrameBufferProperties, GraphicsOutput, Texture, Shader, WindowProperties, NodePath, CardMaker, GraphicsPipe, OrthographicLens
from panda3d.core import loadPrcFileData, Point3
from panda3d.core import AmbientLight, DirectionalLight, PointLight
from panda3d.core import PTALVecBase2f, PTAFloat
import numpy as np
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode
from panda3d.core import Filename
from panda3d.core import PNMImage
from panda3d.bullet import BulletHeightfieldShape
from panda3d.bullet import ZUp, XUp, YUp
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletCapsuleShape, BulletRigidBodyNode
import random
from panda3d.core import TextNode, PNMImage, Texture, CardMaker
# Load configuration settings to show buffers
#loadPrcFileData("", "show-buffers t")
loadPrcFileData("", "notify-level-info")

class riverApp(ShowBase):
    def __init__(self):
        super().__init__()
        # Enable the frame rate meter
        self.setFrameRateMeter(True)
        # Set the window size to 720p
        window_properties = WindowProperties()
        window_properties.set_size(1280, 720)
        self.win.request_properties(window_properties)

        # Disable default camera controls
        self.disableMouse()

        self.cam.set_pos(0, -25*4, 25*4*2)
        self.cam.look_at(0, 0, 0)

        # Create buffers A, B, C, D
        self.buffers = {}
        self.textures = {}
        self.cards = {}
        #for buffer_name in ['A', 'B', 'C', 'D']:
        for buffer_name in ['A', 'B', 'C', 'D']:
            self.create_buffer(buffer_name)

        #base.graphicsEngine.renderFrame()
        # Create the final display quad
        self.create_display_quad()
        # Set the background color to green
        self.win.set_clear_color((1, 1, 1, 1))
        # Add the task to update shaders with time
        sample_texture = self.loader.loadTexture("assets/riversInspo/01_gimpriver.png")
        self.sample_texture_gimp_gradient = self.loader.loadTexture("outfield.png")
        self.cards['A'].set_shader_input("gimpriver", sample_texture)
        self.cards['A'].set_shader_input("gimpgradient", self.sample_texture_gimp_gradient)
        self.cards['A'].set_shader_input("iChannel3", self.textures['D'])  
        self.mouses = PTALVecBase2f()  
        #self.mouses.push_back((0,0))
        self.cards['A'].set_shader_input("iMousePoses", self.mouses)
        self.numMouses = len(self.mouses)
        self.cards['A'].set_shader_input("iMaxRocks", int(self.numMouses))    

        self.cards['B'].set_shader_input("iChannel0", self.textures['A'])

        self.cards['C'].set_shader_input("iChannel0", self.textures['A'])
        self.cards['C'].set_shader_input("iChannel1", self.textures['B'])
        self.cards['C'].set_shader_input("iChannel2", self.textures['C'])
        self.logPoses = PTALVecBase2f()
        self.logVelocities = PTAFloat()
        #self.logPoses.push_back((0,0))
        self.lenlogPoses = len(self.logPoses)
        self.cards['C'].set_shader_input("array_length", self.lenlogPoses)
        self.cards['C'].set_shader_input("iLogPos", self.logPoses)
        self.cards['C'].set_shader_input("iMousePos", (0,0))
        self.cards['C'].set_shader_input("iLogVelocities", self.logVelocities)

        self.cards['D'].set_shader_input("iChannel0", self.textures['A'])
        self.cards['D'].set_shader_input("iChannel2", self.textures['C'])

        self.taskMgr.add(self.update_shaders, "UpdateShadersTask")
        self.accept("v", self.bufferViewer.toggleEnable)
        

        self.logs = []    
        self.random_numbers = [random.uniform(0.1, 2) for _ in range(200)]
        self.setup_physics()
        self.taskMgr.add(self.sampleVelField, "SampleVelFieldTask")
        self.accept("l", self.spawnLog)
        self.taskMgr.add(self.mousePos, "MousePosTask")
        self.rockTimer = 0

        self.taskMgr.doMethodLater(3, self.auto_spawn_log, "AutoSpawnLogTask")
        self.create_text_texture(["How to play:", 
                                  "Left click for pressure disturbance", 
                                  "Right click to spawn barrier", 
                                  "Get as many logs to the end as possible",
                                  "Longer logs score more points"])
        

    

    def create_buffer(self, name):
        """ mybuffer = base.win.makeTextureBuffer(name, 512, 512)
        mytexture = mybuffer.getTexture()
        mytexture.setClearColor((0, 0, 0, 1))
        mytexture.clearImage()
        mybuffer.setSort(-300+len(self.buffers)*10)
        mybuffer.set_clear_color((0, 0, 0, 1))
        #mybuffer.setActive(True) """
        

        mybuffer, mytexture = self.create_offscreen_buffer()
        mytexture.setClearColor((0, 0, 0, 1))
        #mytexture.clearImage()

        myscene = NodePath("My Scene")
        mycamera = base.makeCamera(mybuffer)
        mycamera.reparentTo(myscene)
        
        #make stuff 2d
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setNearFar(-1000, 1000)
        mycamera.node().setLens(lens)
        myscene.setDepthTest(False)
        myscene.setDepthWrite(False)

        # Create a fullscreen quad for the buffer
        card_maker = CardMaker(f"{name}_card")
        card_maker.set_frame_fullscreen_quad()
        card = NodePath(card_maker.generate())
        card.reparent_to(myscene)
        card.setPos(0, 4, 0)
        shader = Shader.load(Shader.SL_GLSL, vertex=f"shaders/{name}_vert.vert", fragment=f"shaders/{name}_frag.frag")
        card.set_shader(shader)
        card.set_shader_input("iResolution", (3*256, 256))
        card.set_shader_input("iTime", 1)
        card.set_shader_input("iTimeDelta", 1)
        
        self.buffers[name] = mybuffer
        self.textures[name] = mytexture
        self.cards[name] = card
        # Toggle manual rendering of the scene
        #mybuffer.set_one_shot(True)
        #base.graphicsEngine.renderFrame()
        #base.win.triggerCopy()
        # put some lighting on the teapot

    def create_offscreen_buffer(self):
        fb_props = FrameBufferProperties()
        fb_props.set_rgba_bits(16, 16, 16, 16)  # Use 16-bit per channel
        #fb_props.set_rgba_bits(8,8,8,8)  # Use 16-bit per channel
        fb_props.set_float_color(True)  # Enable floating-point color buffer
        #fb_props.set_depth_bits(24)
        rez=256
        win_props = WindowProperties.size(3*rez, rez)
        offscreen_buffer = self.graphicsEngine.make_output(
            self.pipe, "offscreen_buffer", -20+len(self.buffers),
            fb_props, win_props,
            GraphicsPipe.BFRefuseWindow, self.win.get_gsg(), self.win
        )

        if not offscreen_buffer:
            return None, None

        render_texture = Texture()
        render_texture.set_format(Texture.F_rgb16)  # Half-float format
        #render_texture.set_format(Texture.F_rgba8)  
        #render_texture.set_component_type(Texture.T_int)  
        #render_texture.set_component_type(Texture.T_short)
        offscreen_buffer.add_render_texture(render_texture, GraphicsOutput.RTMCopyRam)
        #offscreen_buffer.add_render_texture(render_texture, GraphicsOutput.RTMBindOrCopy)

        return offscreen_buffer, render_texture
        

    def create_display_quad(self):
        # Create a quad for the final display
        #quad = self.loader.loadModel("models/plane")
        card_maker = CardMaker("final_card")
        #card_maker.set_frame_fullscreen_quad()
        card_maker.set_frame(-0.5, 0.5, -0.5, 0.5)
        self.quad = NodePath(card_maker.generate())
        self.quad.reparent_to(self.render)
        self.quad.setPos(0,0,0)
        self.quad.setScale(3*64,64,64)
        self.quad.setP(-90)
        #self.quad.set_shader(Shader.load(Shader.SLGLSL, "shaders/A_vert.vert", "shaders/A_frag.frag"))
        self.quad.set_shader(Shader.load(Shader.SL_GLSL, "shaders/final_vert.vert", "shaders/final_frag.frag"))
        #self.quad.set_shader_input("iTime", 1)
        #self.quad.set_shader_input("iTimeDelta", 1)
        self.quad.set_shader_input("iChannel0", self.textures['A'])
        self.quad.set_shader_input("iChannel1", self.textures['B'])
        self.quad.set_shader_input("iChannel2", self.textures['C'])
        #quad.set_shader_input("iChannel3", self.textures['D'])
        #self.quad.set_shader_input("iResolution", (self.win.get_x_size(), self.win.get_y_size()))
        print((self.win.get_x_size(), self.win.get_y_size()))
        #self.quad.set_shader_input("iResolution", (256, 256))
        #self.quad.set_shader_input("iResolution", (1024, 1024))
        #self.quad.setTexture(self.textures['A'],1)
    
    def update_shaders(self, task):
        
        time = globalClock.get_frame_time()
        delta_time = globalClock.get_dt()
        self.cards['A'].set_shader_input("iTime", time)
        self.cards['A'].set_shader_input("iTimeDelta", delta_time)
        #self.cards['A'].set_shader_input("iLogPos", delta_time)
        
        return task.cont
    
    def sampleVelField(self, task):
        # Get the texture's RAM image
        ram_image = self.textures['A'].get_ram_image()

        if ram_image and np.size(ram_image) > 0:
            # Calculate the actual number of components based on the size
            x_size = self.textures['A'].get_x_size()  # 512
            y_size = self.textures['A'].get_y_size()  # 256
            
            # Debug the actual size
            #total_elements = np.size(ram_image) // 2  # Each float16 is 2 bytes
            #elements_per_pixel = total_elements / (x_size * y_size)
            #print(f"Elements per pixel: {elements_per_pixel}")
            
            # Use 4 components instead of 3 - F_rgb16 often includes padding for alignment
            pixel_data = np.frombuffer(ram_image, dtype=np.float32).reshape(y_size, x_size, 4)
            
            # Access just the RGB components
            x=15
            y=128
            
            self.logPoses = PTALVecBase2f()
            self.logVelocities = PTAFloat()
            for n,log in enumerate(self.logs):
                
                #x=int(3*256/2 + log.get_x())
                #y=int(256/2 + log.get_y())
                

                scaled_x = self.scale(log.get_x(), -3*64/2, 3*64/2, 0, 3*256)
                scaled_y = self.scale(log.get_y(), -64/2, 64/2, 0, 256)
                x = int(scaled_x)
                y = int(scaled_y)
                if x < 0 or x >= 3*256 or y < 0 or y >= 256:
                    continue
                #if n==len(self.logs)-1:
                #    self.cards['C'].set_shader_input("iLogPos", (scaled_x/3/256, scaled_y/256))
                self.logPoses.push_back((scaled_x/3/256, scaled_y/256))
                #log.node().set_linear_velocity((pixel_data[y, x, 2], pixel_data[y, x, 1], 0))
                scalar = .05  # Define the scalar value
                velocity = log.node().get_linear_velocity()
                velocity_limit = 15.0  # Define the velocity limit
                self.logVelocities.push_back(min(velocity.length(),15)/15)
                if velocity.length() < velocity_limit:
                    log.node().apply_central_impulse((pixel_data[y, x, 2] * scalar, pixel_data[y, x, 1] * scalar, 0))
                #print(f"log{n},{log.get_x()},{log.get_y()}, Pixel at ({x},{y}): {pixel_data[y, x, :3]}")  # Just RGB (y,x)
                

            self.lenlogPoses = len(self.logPoses)
            self.cards['C'].set_shader_input("array_length", self.lenlogPoses)
            self.cards['C'].set_shader_input("iLogPos", self.logPoses)
            """ max_velocity = max(self.logVelocities) if self.logVelocities else 1.0
            min_velocity = min(self.logVelocities) if self.logVelocities else 0.0
            normalized_velocities = PTAFloat()
            for velocity in self.logVelocities:
                normalized_velocity = (velocity - min_velocity) / (max_velocity - min_velocity)
                normalized_velocities.push_back(normalized_velocity)
            self.logVelocities = normalized_velocities """
            self.cards['C'].set_shader_input("iLogVelocities", self.logVelocities)

            
        return task.cont
    
    def scale(self, value, src_min, src_max, dst_min, dst_max):
        return dst_min + (value - src_min) * (dst_max - dst_min) / (src_max - src_min)
    
    def setup_physics(self):

        # Create the Bullet physics world
        self.physics_world = BulletWorld()
        self.physics_world.set_gravity((0, 0, -9.81))
        # Set default friction for the physics world
        

        # Create a ground plane
        plane_shape = BulletPlaneShape((0, 0, 1), 0)  # Normal vector (0, 0, 1), offset 0
        ground_node = BulletRigidBodyNode('Ground')
        ground_node.add_shape(plane_shape)
        ground_np = self.render.attach_new_node(ground_node)
        ground_np.set_pos(0, 0, 0)
        self.physics_world.attach(ground_node)
        self.bulletTerrain()
        # Create a debug node
        debug_node = BulletDebugNode('Debug')
        debug_node.show_wireframe(True)
        debug_node.show_constraints(True)
        debug_node.show_bounding_boxes(False)
        debug_node.show_normals(False)
        debug_np = self.render.attach_new_node(debug_node)
        debug_np.show()
        self.physics_world.set_debug_node(debug_node)  
        # Add a task to update the physics simulation
        self.taskMgr.add(self.update_physics, "UpdatePhysicsTask")

    def update_physics(self, task):
        dt = globalClock.get_dt()
        self.physics_world.do_physics(dt)
        return task.cont
    
    def bulletTerrain(self):
        # Create a terrain shape
        height = 10.0
        img = PNMImage(Filename('assets/riversInspo/03_gimpriver_scaled.png'))
        shape = BulletHeightfieldShape(img, height, ZUp)
        # Create a terrain node
        terrain_node = BulletRigidBodyNode('Terrain')
        terrain_node.add_shape(shape)
        terrain_np = self.render.attach_new_node(terrain_node)
        terrain_np.set_pos(0, 0, 0)
        self.physics_world.attach(terrain_node)
        return terrain_np
    
    def add_collision_capsule(self):

        # Create a capsule shape
        radius = 0.5
        #height = 2.0
        height = 2.0*self.random_numbers[self.lenlogPoses]
        capsule_shape = BulletCapsuleShape(radius, height, YUp)

        # Create a rigid body node for the capsule
        capsule_node = BulletRigidBodyNode('Capsule')
        capsule_node.add_shape(capsule_shape)
        capsule_node.set_mass(10.0)  # Set the mass of the capsule
        capsule_node.set_friction(0.05)  # Set the friction of the capsule
        # Control the bounce factor (0.0 to 1.0)
        capsule_node.set_restitution(0.4)  # Higher values = bouncier

        # Attach the capsule to the scene
        capsule_np = self.render.attach_new_node(capsule_node)
        capsule_np.set_pos(-3*64/2, -9, 12)  # Position at the origin
        #capsule_np.set_pos(0, 0, 1)  # Position at the origin
        # Set the initial velocity of the capsule
        capsule_node.set_linear_velocity((1, 0, 0))  # Velocity in the x-direction
        capsule_node.set_angular_velocity((0, 0, 0))  # No angular velocity

        # Add the capsule to the physics world
        self.physics_world.attach(capsule_node)

        return capsule_np
    
    def spawnLog(self):
        self.logs.append(self.add_collision_capsule())
        #self.textures['A'].write("outfield.png")
        return
    
    def mousePos(self,task):
        time = task.time
        #surface.setZ(0+sin(time)*3)
        if base.mouseWatcherNode.hasMouse() and (base.mouseWatcherNode.is_button_down("mouse1") or base.mouseWatcherNode.is_button_down("mouse3")) and self.rockTimer < 60:
            x = base.mouseWatcherNode.getMouseX()
            y = base.mouseWatcherNode.getMouseY()
            #print(x,y)
            #surface.set_shader_input("pos", Vec3(base.mouseWatcherNode.getMouseX(),0,base.mouseWatcherNode.getMouseY())*4)
            #pFrom = Point3(0, 0, 0)
            #pTo = Point3(10, 0, 0)

            # Get to and from pos in camera coordinates
            pMouse = base.mouseWatcherNode.getMouse()
            pFrom = Point3()
            pTo = Point3()
            base.camLens.extrude(pMouse, pFrom, pTo)

            # Transform to global coordinates
            pFrom = render.getRelativePoint(base.cam, pFrom)
            pTo = render.getRelativePoint(base.cam, pTo)

            result = self.physics_world.rayTestClosest(pFrom, pTo)

            """ print(result.hasHit())
            print(result.getHitPos())
            print(result.getHitNormal())
            print(result.getHitFraction())
            print(result.getNode()) """
            scaled_x = self.scale(result.getHitPos().x, -3*64/2, 3*64/2, 0, 3*256)
            scaled_y = self.scale(result.getHitPos().y, -64/2, 64/2, 0, 256)
            x = scaled_x/3/256
            y = scaled_y/256
            if base.mouseWatcherNode.is_button_down("mouse1"):
                self.cards['C'].set_shader_input("iMousePos", (x,y))
                self.taskMgr.doMethodLater(1, self.rockUpdate, "RockUpdateTask")
            if base.mouseWatcherNode.is_button_down("mouse3"):
                #self.cards['A'].set_shader_input("iMousePos", (x,y))
                self.mouses.push_back((x,y))
                self.numMouses = len(self.mouses)
                #self.cards['A'].set_shader_input("iMaxRocks", int(self.numMouses))
                #self.cards['A'].set_shader_input("iMousePoses", self.mouses)
                self.taskMgr.doMethodLater(0.5, self.updateRocks, "Ru")
                self.taskMgr.doMethodLater(1, self.rockUpdate, "RockUpdateTask")
                cap = self.add_collision_capsule()
                cap.set_pos(result.getHitPos().x, result.getHitPos().y, 0)
                cap.set_hpr(0,90,0)
                cap.node().set_mass(0)
            self.rockTimer = 100
        return task.cont
    
    def rockUpdate(self,task):
        self.rockTimer = 0
        self.cards['C'].set_shader_input("iMousePos", (1000,1000))
        return task.done
    
    def updateRocks(self,task):
        #self.cards['A'].set_shader_input("iMaxRocks", int(len(self.mouses)))
        #self.cards['A'].set_shader_input("iMousePoses", self.mouses)
        self.cards['A'].set_shader_inputs(
            iMaxRocks = int(len(self.mouses)),
            iMousePoses = self.mouses
        )
        return task.done
    
    def auto_spawn_log(self, task):
        self.spawnLog()
        return task.again
    
    def create_text_texture(self, text_lines):

        # Create a TextNode to hold the text
        text_node = TextNode("text_node")
        text_node.set_text("\n".join(text_lines))
        text_node.set_text_color(1, 1, 1, 1)  # White text
        #text_node.set_align(TextNode.A_center)
        text_node.set_card_color(0, 0, 0, 1)  # Black background
        text_node.set_card_as_margin(0.2, 0.2, 0.2, 0.2)
        text_node.set_card_decal(True)

        # Create a NodePath for the TextNode
        text_np = self.aspect2d.attach_new_node(text_node)
        text_np.set_scale(0.05)  # Scale the text
        text_np.set_pos(-0.8, 0, 0.8)

        """ # Render the text to a texture
        tex = Texture()
        pnm_image = PNMImage(512, 512)
        buffer = self.win.make_texture_buffer("text_buffer", 512, 512)
        buffer.set_clear_color((0, 0, 0, 1))
        camera = self.make_camera(buffer)
        camera.reparent_to(self.aspect2d)
        camera.node().get_display_region(0).set_clear_color_active(True)
        camera.node().get_display_region(0).set_clear_color((0, 0, 0, 1))
        camera.node().set_scene(text_np)
        tex = buffer.get_texture()

        # Create a card to display the texture
        card_maker = CardMaker("text_card")
        card_maker.set_frame(-1, 1, -1, 1)
        card_np = self.render.attach_new_node(card_maker.generate())
        card_np.set_texture(tex)
        card_np.set_pos(0, 0, 0)  # Position the card in the scene
        #card_np. """

        #return card_np
        return
        
    
    


    

    

if __name__ == "__main__":
    app = riverApp()
    app.run()

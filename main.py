from direct.showbase.ShowBase import ShowBase
from panda3d.core import FrameBufferProperties, GraphicsOutput, Texture, Shader, WindowProperties, NodePath, CardMaker, GraphicsPipe, OrthographicLens
from panda3d.core import loadPrcFileData, Point3
from panda3d.core import AmbientLight, DirectionalLight, PointLight
from panda3d.core import PTALVecBase2f, PTAFloat
import numpy as np
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletBoxShape
from panda3d.core import Filename
from panda3d.core import PNMImage
from panda3d.bullet import BulletHeightfieldShape
from panda3d.bullet import ZUp, XUp, YUp
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletCapsuleShape, BulletRigidBodyNode
import random
from panda3d.core import TextNode, PNMImage, Texture, CardMaker
from panda3d.core import BitMask32
from panda3d.core import PGFrameStyle
from direct.task import Task
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

        # Setup background music
        try:
            self.background_music = self.loader.loadMusic("assets/750289__messysloth__maybe-peaceful-sound.wav")
            if self.background_music:
                self.background_music.setLoop(True)
                self.background_music.setVolume(0.5)
                self.background_music.play()
        except Exception as e:
            print(f"Could not load background music: {e}")

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
        
        self.rockBarriers = []
        self.rockBarriersTime = []
        self.logs = []    
        self.random_numbers = [random.uniform(0.1, 2) for _ in range(20000)]
        self.setup_physics()
        self.taskMgr.add(self.sampleVelField, "SampleVelFieldTask")
        self.accept("l", self.spawnLog)
        self.taskMgr.add(self.mousePos, "MousePosTask")
        self.rockTimer = 0

        #self.taskMgr.doMethodLater(3, self.auto_spawn_log, "AutoSpawnLogTask")
        """ self.create_text_texture(["How to play:", 
                                  "esc"]) """
        
        self.MoneyInBank = 100.0
        self.MoneySpent = 0.0
        self.MoneyEarned = 0.0
        self.LogsDelivered = 0
        self.LogsLost = 0
        self.costOfLogsLost = 0.0
        self.waveNr = 0
        self.scoreKeep = self.create_text_texture([#f"Money in bank: {self.MoneyInBank:.2f}",
                             #f"Money spent: {self.MoneySpent:.2f}",
                             f"Current Wave: {self.waveNr}",
                             f"Money earned this wave: {self.MoneyEarned:.2f}",
                             #f"Logs delivered: {self.LogsDelivered}",
                             #f"Total Logs lost: {self.LogsLost}",
                             f"Cost of logs lost this wave: {self.costOfLogsLost:.2f}"])
        
        self.scoreKeep.set_pos(62.0, -38, 0)

        
        self.nextWaveTime = 5
        self.nextWaveCost = 10
        minutes, seconds = divmod(self.nextWaveTime, 60)
        self.waveKeep = self.create_text_texture([f"Wave: {self.waveNr}",
                                                  f"Next wave in: {int(minutes)}:{int(seconds):02d}",
                                                  f"Next wave Cost: {self.nextWaveCost:.2f}",
                                                  f"Money in bank: {self.MoneyInBank:.2f}"])
        self.waveKeep.set_pos(65.0, -20, 12)
        self.taskMgr.add(self.waveControler, "WaveControlerTask")
        #self.taskMgr.doMethodLater(0.5, self.removeOldRocks, "removeOldRocksTask")

        self.accept("r-up", self.restart_game)
        self.gamePaused = False
        self.restarting=False
        self.accept("escape-up", self.escMenu)
        self.accept("q-up", self.exit_game)

    def escMenu(self):
        # Pause the game
        self.gamePaused = not self.gamePaused
        if self.gamePaused:
            self.pausenp = self.create_text_texture(["Menu"])
            self.pausenp.set_pos(0, 16, 14)
            self.pausenp.set_scale(10)

            self.pausenp2 = self.create_text_texture(["Press 'esc' to resume",
                                                            "Press 'r' to restart",
                                                            "Press 'q' to quit"])
            self.pausenp2.set_pos(0, 0, 14)
            self.pausenp2.set_scale(10)

            self.pausenp3 = self.create_text_texture(["How to play:", 
                                  "Left click for pressure disturbance", 
                                  "Right click to spawn barrier", 
                                  "Get as many logs to the end as possible",
                                  "Longer logs score more points"])
            self.pausenp3.set_pos(0, -32, 14)
        else:
            remove_node = self.pausenp.remove_node()
            remove_node = self.pausenp2.remove_node()
            remove_node = self.pausenp3.remove_node()

    def exit_game(self):
        # Clean up resources
        if hasattr(self, 'background_music') and self.background_music:
            self.background_music.stop()
        # Exit the application
        self.userExit()
        

    def waveControler(self,task):
        task.delayTime = 1
        self.nextWaveTime -= 1
        minutes, seconds = divmod(self.nextWaveTime, 60)
        self.waveKeep.node().set_text("\n".join([f"Wave: {self.waveNr}",
                              f"Next wave in: {int(minutes)}:{int(seconds):02d}",
                              f"Next wave Cost: {self.nextWaveCost:.2f}",
                                                  f"Money in bank: {self.MoneyInBank:.2f}"]))
        if self.nextWaveTime <= 0:
            self.waveNr += 1
            self.nextWaveTime = 100
            self.taskMgr.doMethodLater(3, self.auto_spawn_log, "AutoSpawnLogTask")
            self.MoneyInBank = self.MoneyInBank + self.MoneyEarned - self.nextWaveCost - self.costOfLogsLost
            self.MoneyEarned = 0.0
            self.nextWaveCost += 10
            self.MoneySpent += self.nextWaveCost
            self.costOfLogsLost = 0.0
            self.updateScore()

            if self.MoneyInBank < 0:
                self.gameOvertnp = self.create_text_texture(["Game Over"])
                self.gameOvertnp.set_pos(0, 0, 12)
                self.gameOvertnp.set_scale(10)

                self.restart_game_tnp = self.create_text_texture(["Press 'r' to restart"])
                self.restart_game_tnp.set_pos(0, -16, 12)
                self.restart_game_tnp.set_scale(10)
                #self.taskMgr.remove("UpdatePhysicsTask")
                self.taskMgr.remove("AutoSpawnLogTask")
                self.taskMgr.doMethodLater(1, self.end_game, "restart_game")
                self.waveKeep.node().set_text("\n".join([f"Wave: {self.waveNr}",
                              f"Next wave in: {int(minutes)}:{int(seconds):02d}",
                              f"Next wave Cost: {self.nextWaveCost:.2f}",
                              f"Money in bank: {self.MoneyInBank:.2f}"]))
                return task.done
            
        return task.again
    
    def end_game(self,task):
        # Clean up all tasks
        self.taskMgr.remove("UpdateShadersTask")
        self.taskMgr.remove("SampleVelFieldTask")
        self.taskMgr.remove("MousePosTask")
        self.taskMgr.remove("WaveControlerTask")
        self.taskMgr.remove("UpdatePhysicsTask")
        self.taskMgr.remove("AutoSpawnLogTask")
        self.taskMgr.remove("RockUpdateTask")
        self.taskMgr.remove("Ru")
        self.taskMgr.remove("removeOldRocksTask")
        return task.done

    def clearMouses(self,task):
        self.mouses.clear()
        self.mouses = PTALVecBase2f()
        
        
        return task.done

    def restart_game(self):
        # Clean up all tasks
        self.taskMgr.remove("UpdateShadersTask")
        self.taskMgr.remove("SampleVelFieldTask")
        #self.taskMgr.remove("MousePosTask")
        self.restarting=True
        self.taskMgr.remove("WaveControlerTask")
        self.taskMgr.remove("UpdatePhysicsTask")
        self.taskMgr.remove("AutoSpawnLogTask")
        #self.taskMgr.remove("RockUpdateTask")
        self.taskMgr.remove("Ru")
        self.taskMgr.remove("removeOldRocksTask")
        try:
            self.gameOvertnp.remove_node()
            self.restart_game_tnp.remove_node()
        except:
            print("first restart")

        try:
            remove_node = self.pausenp.remove_node()
            remove_node = self.pausenp2.remove_node()
            remove_node = self.pausenp3.remove_node()
        except:
            pass
        self.gamePaused = False

        for r in range(len(self.rockBarriers)):
            #self.mouses.pop_back()
            #self.mouses.set_element(r, (0,0))
            self.physics_world.remove(self.rockBarriers[0].node())
            self.rockBarriers[0].remove_node()
            self.rockBarriers.pop(0)
            self.rockBarriersTime.pop(0)
        
        self.mouses.clear()
        
        """ for rb in self.rockBarriers:
            self.physics_world.remove(rb.node())
            rb.remove_node()
        self.rockBarriers = []
        self.mouses = PTALVecBase2f() """
        self.mouses.push_back((0,0))
        self.mouses.push_back((0,0))
        self.mouses.push_back((0,0))
        self.mouses.push_back((0,0))
        self.mouses.push_back((0,0))
        self.mouses.push_back((0,0))
        self.mouses.push_back((0,0))
        #self.mouses = PTALVecBase2f()  # Reinitialize the array
        self.taskMgr.doMethodLater(.1, self.updateRocks, "updaterocksrestart")
        #self.mouses.pop_back()
        self.taskMgr.doMethodLater(0.3, self.clearMouses, "clearMouses")
        #self.updateRocks

        for log in self.logs:
            self.physics_world.remove(log.node())
            log.remove_node()
        # Reset game variables
        self.MoneyInBank = 100.0
        self.MoneySpent = 0.0
        self.MoneyEarned = 0.0
        self.LogsDelivered = 0
        self.LogsLost = 0
        self.costOfLogsLost = 0.0
        self.waveNr = 0
        self.nextWaveTime = 3
        self.nextWaveCost = 0
        self.logs = []
        self.rockBarriers = []
        self.rockBarriersTime = []
        self.logsInGoal = []
        self.lig = {'outBox': [], 'negBox1': [], 'negBox2': []}

        # Update UI elements
        self.updateScore()
        minutes, seconds = divmod(self.nextWaveTime, 60)
        self.waveKeep.node().set_text("\n".join([f"Wave: {self.waveNr}",
                                                  f"Next wave in: {int(minutes)}:{int(seconds):02d}",
                                                  f"Next wave Cost: {self.nextWaveCost:.2f}",
                                                  f"Money in bank: {self.MoneyInBank:.2f}"]))
        self.goalBox.node().get_child(0).set_text("\n".join(["Goal, Sawmill", "Score: 0"]))
        self.goalBox_neg1.node().get_child(0).set_text("\n".join([f"Lost logs: 0"]))
        self.goalBox_neg2.node().get_child(0).set_text("\n".join([f"Lost logs: 0"]))

        # Restart tasks
        """ self.taskMgr.add(self.update_shaders, "UpdateShadersTask")
        self.taskMgr.add(self.sampleVelField, "SampleVelFieldTask")
        self.taskMgr.add(self.mousePos, "MousePosTask")
        self.taskMgr.add(self.waveControler, "WaveControlerTask")
        self.taskMgr.add(self.update_physics, "UpdatePhysicsTask") """

        self.taskMgr.doMethodLater(.5,self.update_shaders, "UpdateShadersTask")
        self.taskMgr.doMethodLater(.5,self.sampleVelField, "SampleVelFieldTask")
        self.taskMgr.doMethodLater(.5,self.mousePos, "MousePosTask")
        self.taskMgr.doMethodLater(.5,self.waveControler, "WaveControlerTask")
        self.taskMgr.doMethodLater(.5,self.update_physics, "UpdatePhysicsTask")
        #self.taskMgr.doMethodLater(0.5, self.removeOldRocks, "removeOldRocksTask")
        return 

    def updateScore(self):
        self.scoreKeep.node().set_text("\n".join([#f"Money in bank: {self.MoneyInBank:.2f}",
                             #f"Money spent: {self.MoneySpent:.2f}",
                             f"Current Wave: {self.waveNr}",
                             f"Money earned this wave: {self.MoneyEarned:.2f}",
                             #f"Logs delivered: {self.LogsDelivered}",
                             #f"Total Logs lost: {self.LogsLost}",
                             f"Cost of logs lost this wave: {self.costOfLogsLost:.2f}"]))

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
                scalar = .05 * 30 * globalClock.get_dt()  # Define the scalar value to be frame rate independent
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
        ground_np.set_pos(1000, 0, 0)
        self.physics_world.attach(ground_node)
        terrain_np = self.bulletTerrain()
        #self.goalBox = self.add_collision_box()
        self.goalBox = self.add_collision_box(whatbox='outBox',pos=(76, 39, 1),half_extents=(30.5, 5.5, 10.5),t=["Goal, Sawmill", "Score: 0"])
        self.goalBox.node().get_child(0).set_text_color(0.0, 0.4, 0.0, 1)  
        #self.goalBox.node().get_child(0).set_card_color(0, 0, 0, 0.7)  # background
        self.goalBox.node().get_child(0).set_card_color(1, 0, 0, 0)  # background
        self.goalBox_neg1 = self.add_collision_box(whatbox='negBox1',pos=(-50, 39, 1),half_extents=(90.5, 5.5, 10.5),t=[f"Lost logs: 0"])
        self.goalBox_neg2 = self.add_collision_box(whatbox='negBox2',pos=(14, -41, -5),half_extents=(12.5, 5.5, 15.5),t=[f"Lost logs: 0"])
        
        #self.goalBox_neg1.get_child(0).setTransparency(True)
        self.goals = []
        self.goals.append(self.goalBox)
        self.goals.append(self.goalBox_neg1)
        self.goals.append(self.goalBox_neg2)
        # Create a debug node
        debug_node = BulletDebugNode('Debug')
        debug_node.show_wireframe(True)
        debug_node.show_constraints(True)
        debug_node.show_bounding_boxes(False)
        debug_node.show_normals(False)
        #debug_node.show_axes(False)
        debug_np = self.render.attach_new_node(debug_node)
        debug_np.show()
        self.physics_world.set_debug_node(debug_node)  

        # Add a task to update the physics simulation
        self.logsInGoal = []
        l1=[]
        l2=[]
        l3=[]
        self.logsInGoal.append(l1)
        self.logsInGoal.append(l2)
        self.logsInGoal.append(l3)
        self.lig = {}
        self.lig['outBox'] = []
        self.lig['negBox1'] = []
        self.lig['negBox2'] = []
        self.goalBox_neg1.node().get_child(0).set_text_color(0.7, 0, 0, 1)  # Set color to red
        self.goalBox_neg1.node().get_child(0).set_card_color(1, 0, 0, 0)  # Black background
        self.goalBox_neg1.node().get_child(0).set_text("\n".join([f"Lost logs: {len(self.lig[self.goalBox_neg1.node().getName()])}"]))
        self.goalBox_neg2.node().get_child(0).set_text_color(0.7, 0, 0, 1)  # Set color to red
        self.goalBox_neg2.node().get_child(0).set_card_color(1, 0, 0, 0)  # Black background
        """ self.goalBox_neg2.node().get_child(0).set_frame_color(1, 0, 0, 1)  # Red frame
        self.goalBox_neg2.node().get_child(0).set_frame_line_width(2)  # Frame width
        self.goalBox_neg2.node().get_child(0).set_frame_as_margin(0.1, 0.1, 0.1, 0.1)  # Frame margins """
        self.taskMgr.add(self.update_physics, "UpdatePhysicsTask")

        #self.taskMgr.doMethodLater(1.0, self.removeOldRocks, "removeOldRocksTask")

    def update_physics(self, task):
        dt = globalClock.get_dt()
        self.physics_world.do_physics(dt)
        for goal in self.goals:
            result = self.physics_world.contact_test(goal.node())
            for contact in result.getContacts():
                self.goalCol(contact)
        return task.cont
    
    def goalCol(self,contact):
        if "Terrain" in contact.getNode1().getName():
            return
        if "Ground" in contact.getNode1().getName():
            return
        if contact.getNode1() in self.logsInGoal:
            return
        self.logsInGoal.append(contact.getNode1())
        self.lig[contact.getNode0().getName()].append(contact.getNode1())
        #if "outBox" in contact.getNode0().getName():
            #self.goal_text_node.set_text("\n".join(["Outfield", f"Score: {len(self.logsInGoal)}"]))
        #contact.getNode0().get_parent(0).find('**/*text*').node().set_text("\n".join(["Outfield", f"Score: {len(self.logsInGoal)}"]))
        #contact.getNode0().get_child(0).set_text("\n".join(["Outfield", f"Score: {len(self.logsInGoal)}"]))
        if 'neg' in contact.getNode0().getName():
            contact.getNode0().get_child(0).set_text("\n".join([f"Lost logs: {len(self.lig[contact.getNode0().getName()])}"]))
            contact.getNode0().get_child(0).set_text_color(1, 0, 0, 1)  # Set color to red
            contact.getNode0().get_child(0).set_card_color(1, 0, 0, 0)  # Black background
            self.LogsLost += 1
            self.costOfLogsLost += contact.getNode1().get_mass()*.5
            
            
        else:
            contact.getNode0().get_child(0).set_text("\n".join(["Goal, Sawmill", f"Score: {len(self.lig[contact.getNode0().getName()])}"]))
            self.LogsDelivered += 1
            self.MoneyEarned += contact.getNode1().get_mass()

        
        self.updateScore()
        # Check if the node has children and remove them first
        while contact.getNode1().get_num_children() > 0:
            child_np = NodePath(contact.getNode1().get_child(0))
            child_np.remove_node()  # Remove child using NodePath

        self.physics_world.remove(contact.getNode1())
        #contact.getNode1().set_into_collide_mask(BitMask32.all_off())

        """ print(contact.getNode0())
        print(contact.getNode1())

        mpoint = contact.getManifoldPoint()
        print(mpoint.getDistance())
        print(mpoint.getAppliedImpulse())
        print(mpoint.getPositionWorldOnA())
        print(mpoint.getPositionWorldOnB())
        print(mpoint.getLocalPointA())
        print(mpoint.getLocalPointB()) """
    
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
        capsule_node.set_mass(7.5*self.random_numbers[self.lenlogPoses])  # Set the mass of the capsule
        capsule_node.set_friction(0.05)  # Set the friction of the capsule
        # Control the bounce factor (0.0 to 1.0)
        capsule_node.set_restitution(0.4)  # Higher values = bouncier

        # Attach the capsule to the scene
        capsule_np = self.render.attach_new_node(capsule_node)
        #capsule_np.set_pos(-3*64/2, -9, 12)  # very good positions
        capsule_np.set_pos(-3*64/2+random.random()*5, -9+random.random()*19, 12)  # Position at the origin
        #capsule_np.set_pos(0, 0, 1)  # Position at the origin
        # Set the initial velocity of the capsule
        capsule_node.set_linear_velocity((1, 0, 0))  # Velocity in the x-direction
        capsule_node.set_angular_velocity((0, 0, 0))  # No angular velocity

        # Add the capsule to the physics world
        self.physics_world.attach(capsule_node)

        """ trunk = self.loader.loadModel("assets/blender/log.egg")
        trunk.reparentTo(capsule_np)
        trunk.setH(90)
        trunk.setScale(height+.1,8,8) """

        return capsule_np
    
    def add_collision_box(self,whatbox='outBox',pos=(-50, 32, 1),half_extents=(17.5, 5.5, 10.5),t=["Outfield", "Score: 0"]):

        # Create a box shape
        #half_extents = ()
        box_shape = BulletBoxShape(half_extents)

        # Create a rigid body node for the box
        box_node = BulletRigidBodyNode(whatbox)
        box_node.add_shape(box_shape)
        box_node.set_mass(0.0)
        box_node.set_kinematic(True)  # Make the box kinematic (non-solid but still registers collisions)
        box_node.set_into_collide_mask(BitMask32.all_off())

        # Attach the box to the scene
        box_np = self.render.attach_new_node(box_node)
        #box_np.set_pos(76, 32, 1)  
        box_np.set_pos(pos)  
        #box_np.set_hpr(45, 0, 0)  # No rotation

        # Add the box to the physics world
        self.physics_world.attach(box_node)

        goal_text_node = TextNode("text_node")
        goal_text_node.set_text("\n".join(t))
        goal_text_node.set_text_color(1, 1, 1, 1)  # White text
        #text_node.set_align(TextNode.A_center)
        goal_text_node.set_card_color(0, 0, 0, 1)  # Black background
        goal_text_node.set_card_as_margin(0.2, 3.2, 0.2, 0.2)
        goal_text_node.set_card_decal(True)

        # Create a NodePath for the TextNode
        text_np = box_np.attach_new_node(goal_text_node)
        text_np.set_scale(5.0)  # Scale the text
        text_np.set_pos(-17.5, 0, 10.8)
        text_np.set_hpr(0, -90, 0)
        
        return box_np
    
    def spawnLog(self):
        self.logs.append(self.add_collision_capsule())
        if random.random() > 0.75 and self.logs[-1].node().get_mass() < 6 and self.logs[-1].node().get_mass() > 3:
            duck = self.loader.loadModel("assets/blender/duck.egg")
            duck.reparentTo(self.logs[-1])
            duck.setH(90)
            duck.setScale(11.5,11.5,11.5)
            self.logs[-1].node().set_angular_factor((0, 0, 1))
            # Keep the z-axis pointing up by restricting rotation 
            # This constrains rotation to only happen around the y-axis (main axis of log)
              # Allow rotation only around Y axis (log's main axis)



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
                self.taskMgr.doMethodLater(.1, self.rockUpdate, "RockUpdateTask")
            if base.mouseWatcherNode.is_button_down("mouse3"):
                #self.cards['A'].set_shader_input("iMousePos", (x,y))
                if len(self.mouses) >= 5:
                    self.mouses.push_back((x,y))
                    for i in range(5):
                        self.mouses.set_element(i, self.mouses.get_element(i+1))
                    self.mouses.pop_back()
                    self.physics_world.remove(self.rockBarriers[0].node())
                    self.rockBarriers[0].remove_node()
                    self.rockBarriers.pop(0)
                    self.rockBarriersTime.pop(0)
                else:
                    self.mouses.push_back((x,y))
                #self.numMouses = len(self.mouses)
                self.taskMgr.doMethodLater(0.5, self.updateRocks, "Ru")
                self.taskMgr.doMethodLater(.5, self.rockUpdate, "RockUpdateTask")
                cap = self.add_collision_capsule()
                cap.set_pos(result.getHitPos().x, result.getHitPos().y, 0)
                cap.set_hpr(0,90,0)
                cap.node().set_mass(0)
                cap.node().set_kinematic(True)
                self.rockBarriers.append(cap)
                self.rockBarriersTime.append(globalClock.get_frame_time())

            self.rockTimer = 100
        
        if self.restarting:
            self.restarting = False
            return task.done
        return task.cont
    
    def removeOldRocks(self,task):
        
        if len(self.rockBarriersTime)>0:
            if globalClock.get_frame_time() - self.rockBarriersTime[0] > 5:
                #for r in range(len(self.rockBarriers)):
                #self.mouses.pop_back()
                #self.mouses.set_element(r, (0,0))
                """ if len(self.mouses) > 0:
                    for i in range(len(self.mouses)-1):
                        self.mouses.set_element(i, self.mouses.get_element(i+1))
                    self.mouses.pop_back() """
                #self.physics_world.remove(self.rockBarriers[0].node())
                #self.rockBarriers[0].remove_node()
                #self.rockBarriers.pop(0)
                #self.rockBarriersTime.pop(0)
                #print(len(self.mouses))
                """ if len(self.mouses) <= 0:
                    self.mouses.push_back((0,0))
                    #self.taskMgr.doMethodLater(.1, self.updateRocks, "updaterocksremove")
                    self.mouses.pop_back() """
                

                self.mouses.push_back((0,0))
                for i in range(len(self.mouses)-2):
                    self.mouses.set_element(i, self.mouses.get_element(i+1))
                self.mouses.pop_back()

                # Create a new array with fixed length 5
                new_mouses = PTALVecBase2f()
                # Add 5 initial elements (we'll overwrite them)
                for _ in range(5):
                    new_mouses.push_back((0,0))
                    
                # Shift elements: copy up to 4 elements from the current array
                for i in range(min(4, len(self.mouses)-1)):
                    new_mouses.set_element(i, self.mouses.get_element(i+1))
                    
                # Replace current array with the new fixed-length array
                self.mouses = new_mouses
                self.rockBarriers[0].set_pos(0,0,0)

                self.taskMgr.doMethodLater(.1, self.updateRocks, "updaterocksremove")

        return task.again
    
    def rockUpdate(self,task):
        self.rockTimer = 0
        self.cards['C'].set_shader_input("iMousePos", (1000,1000))
        return task.done
    
    def updateRocks(self,task):
        #self.cards['A'].set_shader_input("iMaxRocks", int(len(self.mouses)))
        #self.cards['A'].set_shader_input("iMousePoses", self.mouses)
        #self.mouses.push_back((0,0))
        self.cards['A'].set_shader_inputs(
            iMaxRocks = int(len(self.mouses)),
            iMousePoses = self.mouses
        )
        #self.mouses.pop_back()
        return task.done
    
    def auto_spawn_log(self, task):
        if self.lenlogPoses < 20*self.waveNr:
            self.spawnLog()
        return task.again
    
    def create_text_texture(self, text_lines):

        # Create a TextNode to hold the text
        text_node = TextNode("text_node")
        text_node.set_text("\n".join(text_lines))
        text_node.set_text_color(1, 1, 1, 1)  # White text
        text_node.set_align(TextNode.A_center)
        text_node.set_card_color(0, 0, 0, 1)  # Black background
        text_node.set_card_as_margin(0.2, 0.2, 0.2, 0.2)
        text_node.set_card_decal(True)
        text_node.set_frame_as_margin(0.1, 0.1, 0.1, 0.1)
        text_node.set_frame_color(0, 0, 1, 1)
        text_node.set_frame_line_width(4)

        # Create a NodePath for the TextNode
        text_np = self.render.attach_new_node(text_node)
        text_np.set_scale(4.0)  # Scale the text
        text_np.set_pos(-60.0, -40, 0)
        text_np.set_hpr(0, -90, 0)

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
        return text_np
        
    
    


    

    

if __name__ == "__main__":
    app = riverApp()
    app.run()

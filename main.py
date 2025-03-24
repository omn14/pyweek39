from direct.showbase.ShowBase import ShowBase
from panda3d.core import FrameBufferProperties, GraphicsOutput, Texture, Shader, WindowProperties, NodePath, CardMaker, GraphicsPipe, OrthographicLens
from panda3d.core import loadPrcFileData
from panda3d.core import AmbientLight, DirectionalLight, PointLight
import numpy as np
# Load configuration settings to show buffers
loadPrcFileData("", "show-buffers t")

class ShaderToyApp(ShowBase):
    def __init__(self):
        super().__init__()
        # Enable the frame rate meter
        self.setFrameRateMeter(True)

        # Disable default camera controls
        #self.disableMouse()

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
        sample_texture = self.loader.loadTexture("/home/ole/Pictures/girlSeatedInWater_mirror.jpg")
        self.cards['A'].set_shader_input("iChannel3", self.textures['D'])

        self.cards['B'].set_shader_input("iChannel0", self.textures['A'])

        self.cards['C'].set_shader_input("iChannel0", self.textures['A'])
        self.cards['C'].set_shader_input("iChannel1", self.textures['B'])
        self.cards['C'].set_shader_input("iChannel2", self.textures['C'])

        self.cards['D'].set_shader_input("iChannel0", self.textures['A'])
        self.cards['D'].set_shader_input("iChannel2", self.textures['C'])

        self.taskMgr.add(self.update_shaders, "UpdateShadersTask")
        self.accept("v", self.bufferViewer.toggleEnable)
        self.taskMgr.add(self.sampleVelField, "SampleVelFieldTask")
        

    

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
        card_maker.set_frame_fullscreen_quad()
        self.quad = NodePath(card_maker.generate())
        self.quad.reparent_to(self.render)
        self.quad.setPos(0,5,0)
        self.quad.setScale(3,1,1)
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
        #print(delta_time)
        
        #self.buffers['B'].set_clear_color((0, 0, .2, 1))
        self.cards['A'].set_shader_input("iTime", time*0+3.14/2)
        self.cards['A'].set_shader_input("iTimeDelta", delta_time)
        #texture_copy = Texture()
        #texture_copy = self.textures['A'].makeCopy()
        #self.cards['A'].set_shader_input("iChannel3", self.textures['A'])
        #self.cards['A'].set_shader_input("iChannel3", texture_copy)
        

        """ self.cards['B'].set_shader_input("iChannel0", self.textures['A'])

        self.cards['C'].set_shader_input("iChannel0", self.textures['A'])
        self.cards['C'].set_shader_input("iChannel1", self.textures['B'])
        self.cards['C'].set_shader_input("iChannel2", self.textures['C']) """
        
        #self.quad.set_shader_input("iTime", time)
        #self.quad.set_shader_input("iTimeDelta", delta_time)
        #self.quad.set_shader_input("iChannel0", self.textures['A'])
        #self.quad.set_shader_input("iChannel0", self.buffers['A'].getTexture())
        #self.quad.set_shader_input("iChannel1", self.textures['B'])
        #self.quad.set_shader_input("iChannel2", self.textures['C'])
        #self.quad.set_shader_input("iChannel3", self.textures['A'])


        """ self.cards['A'].set_shader_input("iChannel3", self.textures['D'])

        self.cards['B'].set_shader_input("iChannel0", self.textures['A'])

        self.cards['C'].set_shader_input("iChannel0", self.textures['A'])
        self.cards['C'].set_shader_input("iChannel1", self.textures['B'])
        self.cards['C'].set_shader_input("iChannel2", self.textures['C'])

        self.cards['D'].set_shader_input("iChannel0", self.textures['A'])
        self.cards['D'].set_shader_input("iChannel2", self.textures['C']) """
        
        
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
            #print(f"Pixel at ({x},{y}): {pixel_data[y, x, :3]}")  # Just RGB (y,x)
            
        return task.cont
    

if __name__ == "__main__":
    app = ShaderToyApp()
    app.run()

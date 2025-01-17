import wx
from wx.glcanvas import GLCanvas, GLContext
from OpenGL.GL import *
from OpenGL.GLU import *
from Interface.Furniture import Furniture
from Interface.InputManager import InputManager
from Interface.Camera import *
from Interface.Room import Room
import os
import numpy


class MyCanvas(GLCanvas):

    def __init__(self, parent):
        GLCanvas.__init__(self, parent, -1, size=(850, 700), pos=(0, 0))

        # init context
        self.init = False
        self.context = GLContext(self)
        self.SetCurrent(self.context)

        # init objects
        self.room_directories = {}
        self.current_room_name = 'Nothing'
        self.room = None
        self.furniture = {}
        self.camera = Camera()
        self.input = InputManager(850, 700, self.room, self.furniture, self.camera)

        # load rooms and furniture
        # select all the folders in rooms and furniture folders that have one png file and one room file
        # TODO need to handle when those two files aren't png and room

        for root, directory, file in os.walk('../res/Models/rooms'):
            if len(file) == 2:
                png, room = (os.path.join(root, x) for x in file)
                self.add_room_directory(png, room, file[0].split('.')[0])

        for root, directory, file in os.walk('../res/Models/furniture'):
            if len(file) == 2:
                obj, png = (os.path.join(root, x) for x in file)
                self.add_furniture(png, obj, file[0].split('.')[0])

        # init canvas
        glClearColor(42/256, 49/256, 50/256, 0.8)
        # glClearDepth(1)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        self.resize(None)

        # bind function
        self.Bind(wx.EVT_SIZE, self.resize)
        self.Bind(wx.EVT_PAINT, self.paint)
        self.Bind(wx.EVT_KEY_DOWN, self.input.keyboard)
        self.Bind(wx.EVT_KEY_UP, self.input.keyboard_up)
        self.Bind(wx.EVT_MOTION, self.input.mouse_passive_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.input.mouse_wheel_func)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

    def OnIdle(self, event):
        self.Refresh()

    def paint(self, event):
        self.display()

    def display(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, -700/4, -1000.0)

        self.camera.update_position()
        for x in self.furniture:
            self.furniture[x].update_position()

        # draw block in coordinate of the room
        glPushMatrix()
        glTranslatef(self.camera.xPosition, self.camera.yPosition, self.camera.zPosition)
        glRotatef(self.camera.yawSpinAngle, 0, True, 0)

        if not self.current_room_name == 'Nothing':
            glPushMatrix()
            glScale(6.0, 6.0, 6.0)
            self.room.draw()
            glPopMatrix()

        for x in self.furniture:
            if self.furniture[x].is_shown():
                glPushMatrix()
                glScale(self.furniture[x].scale, self.furniture[x].scale, self.furniture[x].scale)
                glTranslatef(self.furniture[x].xPosition, self.furniture[x].yPosition+10, self.furniture[x].zPosition)
                glRotatef(self.furniture[x].yawSpinAngle, 0, True, 0)

                self.furniture[x].draw()

                glPopMatrix()

        glPopMatrix()

        self.SwapBuffers()

    def resize(self, event):

        size = self.GetClientSize()
        glViewport(0, 0, size.width, size.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(size.width)/float(size.height), 0.1, 30000.0)

    # i combine png and room files into one string separated by '*'
    def change_room(self, room_name, is_scanning=False):

        del self.room

        if not room_name == 'Nothing':
            png_file, room_file = self.room_directories[room_name].split('*')
            self.room = Room(png_file, room_file, is_scanning)

        else:
            self.room = None

        self.current_room_name = room_name

    def add_room_directory(self, png_file, room_file, room_name):

        dirs = '*'.join([png_file,room_file])   # combine two file directories into one string for easy control
        self.room_directories.update({room_name: dirs})     # update dictionary of room directories

    def create_a_scanning_room(self):           # create an empty room to start scanning
        self.room = Room(new_scan=True)
        self.current_room_name = 'New room'     # this name is arbitrary, I just switch it to 'New room' so that
        # function room.draw() can be called # TODO need to get around this

        # init a black texture file
        self.room.image = numpy.zeros((self.room.texture_size[0], self.room.texture_size[1], 4), numpy.uint8)
        self.room.texture_data = numpy.zeros((self.room.texture_size[0]*self.room.texture_size[1], 4), numpy.uint8)

    def add_furniture(self, png_file, obj_file, furniture_name):
        self.furniture.update({furniture_name: Furniture(png_file, obj_file)})

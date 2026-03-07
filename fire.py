from PyQt6.QtWidgets import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np


# Global variables
NUM_PARTICLES = 100
FIRE_RADIUS = 0.15
WIND_AMPLITUDE = 0.5
WIND_FREQUENCY = 1.5
WIND_SPEED = 5
WIND = False
ROTATE = False
ALPHA = 3


### Global functions
def toggleWind():
    """ Toggles wind """
    global WIND
    if WIND:
        WIND = False
    else:
        WIND = True

def toggleRotate():
    """ Toggles rotation """
    global ROTATE
    if ROTATE:
        ROTATE = False
    else:
        ROTATE = True

def setRadius(radius):
    """ Sets FIRE_RADIUS to radius """
    global FIRE_RADIUS
    FIRE_RADIUS = radius

def setParticleNum(num):
    """ Sets NUM_PARICLES to num """
    global NUM_PARTICLES
    NUM_PARTICLES = num

def setWindSpeed(speed):
    """ Sets WIND_FREQUENCY to freq """
    global WIND_SPEED
    WIND_SPEED = speed

def setAlpha(val):
    """ Sets ALPHA to val """
    global ALPHA
    ALPHA = val




class Particle:
    """ Particle class """
    def __init__(self, position: np.array, velocity, size, lifespan):
        """ Initialize particle """
        self.pos = position                                         # Position
        self.vel = velocity                                         # Velocity
        self.acc = np.array([0, 0, 0])                              # Acceleration (0)
        self.color = [1.0, 0.6, 0.0]                                # Color (yellow) + transparnecy
        self.startSize = size                                       # Starting size
        self.size = size                                            # Current size
        self.lifespan = lifespan                                    # Lifespan
        self.age = 0                                                # Age (0)

    def isDead(self):
        """ Returns true if the particle has died, false otherwise """
        return self.lifespan <= 0 or self.size <= 0
    
    def update(self, time, timePrev):
        """ Updates particle state based on time and previous time """
        timeStep = time - timePrev
        self._updateAcc(time)
        self._updateVel(timeStep)
        self.pos += self.vel * timeStep

        self._updateVisual(timeStep)

    def _updateVel(self, time):
        """ Updates velocity based on time step """
        self.vel += self.acc * time

    def _updateAcc(self, time):
        """ Updates acceleration based on time step """
        self.acc[1] = -0.05                         # Gravity
        self.acc[0] = np.random.uniform(-0.5, 0.5)  # X turbulence
        self.acc[2] = np.random.uniform(-0.5, 0.5)  # Z turbulence

        if (WIND):                                  # Wind
            windY = getWind(time)
            if (self.pos[1] > windY - 0.1 and self.pos[1] < windY + 0.1):
                self.acc[0] += WIND_SPEED

    def _updateVisual(self, time):
        """ Updates size, lifespan, age, and color """
        self.size = self.startSize * ((self.lifespan - self.age) / self.lifespan)
        self.lifespan -= time
        self.age += time
        newColor = calculateColor(self.lifespan, self.age)
        self.color = [newColor[0], newColor[1], newColor[2], np.random.uniform(0.5 / ALPHA, 0.8 / ALPHA)]

class Fire:
    """ Fire system class """
    def __init__(self, center):
        """ Initializes fire """
        self.center = center    # Origin of flame
        self.particles = []     # List of existing particles
        self.time = 0           # Time

    def addParticle(self):
        """ Adds a new particle """
        self.particles.append(createParticle(self.center))

    def update(self):
        """ Updates fire and its particles """
        timePrev = self.time    # Get time
        self.time += 0.01

        if len(self.particles) < (NUM_PARTICLES + np.random.uniform(-1, 1) * 20):
            self.addParticle()                      # Add particle
            
        for particle in self.particles:             # Update particles
            particle.update(self.time, timePrev)
            if particle.isDead():                   # Remove particle if dead and replace it
                self.particles.remove(particle)
                self.addParticle()

    def draw(self):
        """ Render flame with PyOpenGL """
        for particle in self.particles:
            glPushMatrix()

            glColor4f(particle.color[0], particle.color[1], particle.color[2], particle.color[3])   # Color
            glTranslatef(particle.pos[0], particle.pos[1], particle.pos[2])                         # Location
            quadric = gluNewQuadric()
            gluSphere(quadric, particle.size, 16, 16)
            glColor4f(particle.color[0], particle.color[1], particle.color[2], particle.color[3])   # Glow
            for i in range(ALPHA):                                                              
                quadric = gluNewQuadric()
                gluSphere(quadric, particle.size*(i + 1), 16, 16)

            glPopMatrix()

    def removeParticles(self):
        """ Removes extraneous particles """
        self.particles = self.particles[0:NUM_PARTICLES]




### Helper functions
def getWind(time):
    """ Returns y-position of wind sinusoidal and draws its location """
    windY = WIND_AMPLITUDE * np.sin(WIND_FREQUENCY * time) + 0.7

    glPushMatrix()
    glColor3f(255, 255, 255)
    glTranslatef(-1, windY, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.1, 16, 16)
    glPopMatrix()

    return windY

def createParticle(center):
    """ Creates particle and assigns its initial values """
    pos = center + randomPoint(center, FIRE_RADIUS)
    vel = np.array([0.0, np.random.uniform(0.5, 1.5), 0.0], dtype=np.float32)
    size = np.random.uniform(0.02, 0.05)
    lifespan = np.random.uniform(1.5, 2.0)
    return Particle(pos, vel, size, lifespan)

def randomPoint(center, radius):
    """ Calculates a random point in a circle based on its center and radius """
    theta = 2 * np.pi * np.random.uniform(0, 1)
    phi = np.arccos(1 - 2 * np.random.uniform(0, 1))
    distance = radius * np.sqrt(np.random.uniform(0, 1))

    x = center[0] + distance * np.sin(phi) * np.cos(theta)
    y = center[1] + distance * np.sin(phi) * np.sin(theta)
    z = center[2] + distance * np.cos(phi)

    return np.array([x, y, z])

def calculateColor(lifespan, age):
    """ Calculates a color based on life time remaining """
    yellow = np.array([1.0, 0.6, 0.0])
    orange = np.array([1.0, 0.2, 0.0])
    remainingLife = lifespan - age

    return yellow * remainingLife + orange * (1 - remainingLife)




### UI Widgets
class GLWindow(QOpenGLWidget):
    """ OpenGL window """
    def __init__(self, parent=None):
        """ Initializes widget """
        super(GLWindow, self).__init__(parent)
        self.fire = Fire(np.array([0.0, 0.0, 0.0]))

    def initializeGL(self):
        """ Sets up GL rendering """
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(3)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, 1, 0.1, 50.0)
        
        glTranslatef(0.0, -1.0, -7.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        """ Draws GL by updating fire state """
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.fire.update()
        self.fire.draw()

        if (ROTATE):    # Camera rotation
            glRotate(0.5, 0, 1, 0)

        self.update()

class Window(QWidget):
    """ UI window """
    def __init__(self):
        """ Initializes widget """
        super(Window, self).__init__()
        self.glWidget = GLWindow()                                      # GL render

        self.rotateToggle = QCheckBox("rotate")                         # Rotation toggle
        self.rotateToggle.stateChanged.connect(self._toggleRotation)

        self.windToggle = QCheckBox("wind")                             # Wind toggle
        self.windToggle.stateChanged.connect(self._toggleWind)

        self.wind = False                                               # Wind indicator
        self.windLabel = QLabel()                                       # Wind frequency slider
        self.windLabel.setText("wind speed")
        self.windSpeed = QSlider()
        self.windSpeed.setMinimum(1)
        self.windSpeed.setMaximum(10)
        self.windSpeed.setSingleStep(1)
        self.windSpeed.setValue(5)
        self.windSpeed.setOrientation(Qt.Orientation.Horizontal)
        self.windSpeed.setMinimumSize(150, 20)
        self.windSpeed.sliderMoved.connect(self._updateWindSpeed)

        fireLabel = QLabel()                                            # Fire radius slider
        fireLabel.setText("fire radius")
        self.fireRad = QSlider()
        self.fireRad.setMinimum(1)
        self.fireRad.setMaximum(10)
        self.fireRad.setSingleStep(1)
        self.fireRad.setValue(3)
        self.fireRad.setOrientation(Qt.Orientation.Horizontal)
        self.fireRad.setMinimumSize(150, 20)
        self.fireRad.sliderMoved.connect(self._updateRadius)

        particlesLabel = QLabel()                                       # Particle number slider
        particlesLabel.setText("number of particles")
        self.particleNum = QSlider()
        self.particleNum.setMinimum(50)
        self.particleNum.setMaximum(400)
        self.particleNum.setPageStep(50)
        self.particleNum.setValue(100)
        self.particleNum.setOrientation(Qt.Orientation.Horizontal)
        self.particleNum.setMinimumSize(150, 20)
        self.particleNum.sliderMoved.connect(self._updateParticleNum)

        alphaLabel = QLabel()                                           # Alpha amount slider
        alphaLabel.setText("alpha level")
        self.alphaLevel = QSlider()
        self.alphaLevel.setMinimum(1)
        self.alphaLevel.setMaximum(5)
        self.alphaLevel.setPageStep(1)
        self.alphaLevel.setValue(3)
        self.alphaLevel.setOrientation(Qt.Orientation.Horizontal)
        self.alphaLevel.setMinimumSize(150, 20)
        self.alphaLevel.sliderMoved.connect(self._updateAlpha)
    
        interfaceLayout = QVBoxLayout()                                 # User interface layout
        interfaceLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        interfaceLayout.addWidget(self.rotateToggle)
        interfaceLayout.addWidget(self.windToggle)
        interfaceLayout.addWidget(self.windLabel)
        interfaceLayout.addWidget(self.windSpeed)
        interfaceLayout.addWidget(fireLabel)
        interfaceLayout.addWidget(self.fireRad)
        interfaceLayout.addWidget(particlesLabel)
        interfaceLayout.addWidget(self.particleNum)
        interfaceLayout.addWidget(alphaLabel)
        interfaceLayout.addWidget(self.alphaLevel)
        self.windLabel.hide()
        self.windSpeed.hide()

        mainLayout = QHBoxLayout()                                      # Main window layout
        mainLayout.addWidget(self.glWidget, 3)
        mainLayout.addLayout(interfaceLayout, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle("Fire Particles")

    def _toggleRotation(self):
        """ Toggles rotation """
        toggleRotate()

    def _toggleWind(self):
        """ Toggles wind """
        toggleWind()
        if self.wind:
            self.windLabel.hide()
            self.windSpeed.hide()
            self.wind = False
        else:
            self.windLabel.show()
            self.windSpeed.show()
            self.wind = True

    def _updateRadius(self, val):
        """ Updates radius value """
        radius = 0.05 * val
        setRadius(radius)
        print("radius:", FIRE_RADIUS)

    def _updateParticleNum(self, num):
        """ Updates particle amount """
        setParticleNum(num)
        self.glWidget.fire.removeParticles()
        print("num particles:", NUM_PARTICLES)

    def _updateAlpha(self, num):
        """ Updates alpha value """
        setAlpha(num)
        print("alpha:", ALPHA)

    def _updateWindSpeed(self, num):
        """ Updates alpha value """
        setWindSpeed(num)
        print("wind freq:", WIND_SPEED)

    def resizeEvent(self, e):
        """ Resizes window """
        width = e.size().width()
        if width < 600:
            width = 600
        height = int(width / self.aspect_ratio)
        print(e.size().width(), e.size().height())
        self.resize(width, height)
        return super().resizeEvent(e)
        


if __name__ == "__main__":
    app = QApplication([])
    window = Window() 
    window.setGeometry(100, 100, 800, 600)
    window.aspect_ratio = 4 / 3

    window.show()
    app.exec()
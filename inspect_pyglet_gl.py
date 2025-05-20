import pyglet.gl as gl
import pyglet

print('pyglet.gl attributes:')
print([attr for attr in dir(gl) if 'LoadIdentity' in attr or 'load' in attr.lower()])

print('pyglet.gl.gl attributes:')
print([attr for attr in dir(gl.gl) if 'LoadIdentity' in attr or 'load' in attr.lower()])

print('pyglet version:', pyglet.version)

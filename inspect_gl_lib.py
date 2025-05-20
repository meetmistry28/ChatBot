import pyglet.gl as gl
print('gl.lib.glLoadIdentity:', hasattr(gl.lib, 'glLoadIdentity'))
print('gl.lib.glLoadIdentity pointer:', getattr(gl.lib, 'glLoadIdentity', None))

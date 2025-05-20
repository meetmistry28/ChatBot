import pyglet.gl as gl
print('Has gl.lib:', hasattr(gl, 'lib'))
print('Has gl._lib:', hasattr(gl, '_lib'))
print('Has gl.glLoadIdentity:', hasattr(gl, 'glLoadIdentity'))
if hasattr(gl, 'lib'):
    print('gl.lib attributes:', dir(gl.lib))
if hasattr(gl, '_lib'):
    print('gl._lib attributes:', dir(gl._lib))

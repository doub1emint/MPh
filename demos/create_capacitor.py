﻿"""
Creates the demonstration model "capacitor" from scratch.

The code below uses the higher-level Python layer as much as possible
and falls back to the Java layer when functionality is (still) missing.
"""
__license__ = 'MIT'


import mph
from numpy import array
from jpype import JBoolean


# Create empty model.
client = mph.start()
model = client.create('capacitor')


# Parameters
model.java.param().group('default').name('parameters')
model.parameter('U', '1[V]')
model.description('U', 'applied voltage')
model.parameter('d', '2[mm]')
model.description('d', 'electrode spacing')
model.parameter('l', '10[mm]')
model.description('l', 'plate length')
model.parameter('w', '2[mm]')
model.description('w', 'plate width')


# Functions
functions = model/'functions'
step = functions.create('Step', name='step')
step.property('funcname', 'step')
step.property('location', -0.01)
step.property('smooth', 0.01)


# Component
components = model/'components'
component = components.create(True, name='component')


# Geometry
geometries = model/'geometries'
geometry = geometries.create(2, name='geometry')

anode = geometry.create('Rectangle', name='anode')
anode.property('pos', ['-d/2-w/2', '0'])
anode.property('base', 'center')
anode.property('size', ['w', 'l'])

cathode = geometry.create('Rectangle', name='cathode')
cathode.property('base', 'center')
cathode.property('pos',  ['+d/2+w/2', '0'])
cathode.property('size', ['w', 'l'])

vertices = geometry.create('BoxSelection', name='vertices')
vertices.property('entitydim', 0)

rounded = geometry.create('Fillet', name='rounded')
rounded.property('radius', '1[mm]')
rounded.java.selection('point').named(vertices.tag())

medium1 = geometry.create('Rectangle', name='medium 1')
medium1.property('pos',  ['-max(l,d+2*w)', '-max(l,d+2*w)'])
medium1.property('size', ['max(l,d+2*w)', 'max(l,d+2*w)*2'])

medium2 = geometry.create('Rectangle', name='medium 2')
medium2.property('pos',  ['0', '-max(l,d+2*w)'])
medium2.property('size', ['max(l,d+2*w)', 'max(l,d+2*w)*2'])

axis = geometry.create('Polygon', name='axis')
axis.property('type', 'open')
axis.property('source', 'table')
axis.property('table', [
    ['-d/2', '0'],
    ['-d/4', '0'],
    ['0',    '0'],
    ['+d/4', '0'],
    ['+d/2', '0'],
])

model.java.coordSystem('sys1').label('boundary system')
model.build(geometry)


# Views
views = model/'views'
view = views/'View 1'
view.rename('view')
view.java.axis().label('axis')
view.java.axis().set('xmin', -0.01495)
view.java.axis().set('xmax', +0.01495)
view.java.axis().set('ymin', -0.01045)
view.java.axis().set('ymax', +0.01045)


# Selections
selections = model/'selections'

anode_volume = selections.create('Disk', name='anode volume')
anode_volume.property('posx', '-d/2-w/2')
anode_volume.property('r', 'w/10')

anode_surface = selections.create('Adjacent', name='anode surface')
anode_surface.property('input', [anode_volume.tag()])

cathode_volume = selections.create('Disk', name='cathode volume')
cathode_volume.property('posx', '+d/2+w/2')
cathode_volume.property('r', 'w/10')

cathode_surface = selections.create('Adjacent', name='cathode surface')
cathode_surface.property('input', [cathode_volume.tag()])

medium1 = selections.create('Disk', name='medium 1')
medium1.property('posx', '-2*d/10')
medium1.property('r', 'd/10')

medium2 = selections.create('Disk', name='medium 2')
medium2.property('posx', '+2*d/10')
medium2.property('r', 'd/10')

media = selections.create('Union', name='media')
media.property('input', [medium1.tag(), medium2.tag()])

domains = selections.create('Explicit', name='domains')
domains.java.all()

exterior = selections.create('Adjacent', name='exterior')
exterior.property('input', [domains.tag()])

axis = selections.create('Box', name='axis')
axis.property('entitydim', 1)
axis.property('xmin', '-d/2-w/10')
axis.property('xmax', '+d/2+w/10')
axis.property('ymin', '-l/20')
axis.property('ymax', '+l/20')
axis.property('condition', 'inside')

center = selections.create('Disk', name='center')
center.property('entitydim', 0)
center.property('r', 'd/10')

probe1 = selections.create('Disk', name='probe 1')
probe1.property('entitydim', 0)
probe1.property('posx', '-d/4')
probe1.property('r', 'd/10')

probe2 = selections.create('Disk', name='probe 2')
probe2.property('entitydim', 0)
probe2.property('posx',      '+d/4')
probe2.property('r',         'd/10')


# Physics
physics = model/'physics'

es = physics.create('Electrostatics', geometry.tag(), name='electrostatic')
es.java.field('electricpotential').field('V_es')
es.java.selection().named(media.tag())
es.java.prop('d').set('d', 'l')
es.java.feature('ccn1').label('Laplace equation')
es.java.feature('zc1').label('zero charge')
es.java.feature('init1').label('initial values')
anode = es.create('ElectricPotential', 1, name='anode')
anode.java.selection().named(anode_surface.tag())
anode.property('V0', '+U/2')
cathode = es.create('ElectricPotential', 1, name='cathode')
cathode.java.selection().named(cathode_surface.tag())
cathode.property('V0', '-U/2')

ec = physics.create('ConductiveMedia', geometry.tag(), name='electric currents')
ec.java.field('electricpotential').field('V_ec')
ec.java.selection().named(media.tag())
ec.java.prop('d').set('d', 'l')
ec.java.feature('cucn1').label('current conservation')
ec.java.feature('ein1').label('insulation')
ec.java.feature('init1').label('initial values')
anode = ec.create('ElectricPotential', 1, name='anode')
anode.java.selection().named(anode_surface.tag())
anode.property('V0', '+U/2*step(t[1/s])')
cathode = ec.create('ElectricPotential', 1, name='cathode')
cathode.java.selection().named(cathode_surface.tag())
cathode.property('V0', '-U/2*step(t[1/s])')


# Materials
materials = model/'materials'

medium1 = materials.create('Common', name='medium 1')
medium1.java.selection().named((model/'selections'/'medium 1').tag())
medium1.java.propertyGroup('def').set('relpermittivity',
    ['1', '0', '0', '0', '1', '0', '0', '0', '1'])
medium1.java.propertyGroup('def').set('relpermittivity_symmetry', '0')
medium1.java.propertyGroup('def').set('electricconductivity',
    ['1e-10', '0', '0', '0', '1e-10', '0', '0', '0', '1e-10'])
medium1.java.propertyGroup('def').set('electricconductivity_symmetry', '0')

medium2 = materials.create('Common', name='medium 2')
medium2.java.selection().named((model/'selections'/'medium 2').tag())
medium2.java.propertyGroup('def').set('relpermittivity',
    ['2', '0', '0', '0', '2', '0', '0', '0', '2'])
medium2.java.propertyGroup('def').set('relpermittivity_symmetry', '0')
medium2.java.propertyGroup('def').set('electricconductivity',
    ['1e-10', '0', '0', '0', '1e-10', '0', '0', '0', '1e-10'])
medium2.java.propertyGroup('def').set('electricconductivity_symmetry', '0')


# Studies
studies = model/'studies'
solutions = model/'solutions'

study = studies.create(name='static')
study.java.setGenPlots(False)
study.java.setGenConv(False)
step = study.create('Stationary', name='stationary')
step.property('activate', [
    (physics/'electrostatic').tag(), 'on',
    (physics/'electric currents').tag(), 'off',
    'frame:spatial1', 'on',
    'frame:material1', 'on',
])
solution = solutions.create(name='electrostatic solution')
solution.java.study(study.tag())
solution.java.attach(study.tag())
solution.create('StudyStep', name='equations')
solution.create('Variables', name='variables')
solver = solution.create('Stationary', name='stationary solver')
solver.java.feature('fcDef').label('fully coupled')
solver.java.feature('aDef').label('advanced options')
solver.java.feature('dDef').label('direct solver')

study = studies.create(name='relaxation')
study.java.setGenPlots(False)
study.java.setGenConv(False)
step = study.create('Transient', name='time-dependent')
step.property('tlist', 'range(0, 0.01, 1)')
step.property('activate', [
    (physics/'electrostatic').tag(), 'off',
    (physics/'electric currents').tag(), 'on',
    'frame:spatial1', 'on',
    'frame:material1', 'on',
])
solution = solutions.create(name='time-dependent solution')
solution.java.study(study.tag())
solution.java.attach(study.tag())
solution.create('StudyStep', name='equations')
variables = solution.create('Variables', name='variables')
variables.property('clist', ['range(0, 0.01, 1)', '0.001[s]'])
solver = solution.create('Time', name='time-dependent solver')
solver.property('tlist', 'range(0, 0.01, 1)')
solver.java.feature('fcDef').label('fully coupled')
solver.java.feature('aDef').label('advanced options')
solver.java.feature('dDef').label('direct solver')

study = studies.create(name='sweep')
study.java.setGenPlots(False)
study.java.setGenConv(False)

step = study.create('Parametric', name='parameter sweep')
step.property('pname', ['d'])
step.property('plistarr', ['1 2 3'])
step.property('punit', ['mm'])

step = study.create('Transient', name='time-dependent')
step.property('activate', [
    (physics/'electrostatic').tag(), 'off',
    (physics/'electric currents').tag(), 'on',
    'frame:spatial1', 'on',
    'frame:material1', 'on',
])

step.property('tlist', 'range(0, 0.01, 1)')

solution = solutions.create(name='parametric solution')
solution.java.study(study.tag())
solution.java.attach(study.tag())
solution.create('StudyStep', name='equations')
variables = solution.create('Variables', name='variables')
variables.property('clist', ['range(0, 0.01, 1)', '0.001[s]'])
solver = solution.create('Time', name='time-dependent solver')
solver.property('tlist', 'range(0, 0.01, 1)')
solver.java.feature('fcDef').label('fully coupled')
solver.java.feature('aDef').label('advanced options')
solver.java.feature('dDef').label('direct solver')

sols = solutions.create(name='parametric solutions')
sols.java.study(study.tag())
model.java.batch().create('p1', 'Parametric')
model.java.batch('p1').create('so1', 'Solutionseq')
model.java.batch('p1').study(study.tag())
model.java.batch('p1').label('parametric sweep')
model.java.batch('p1').set('control',
    (model/'studies'/'sweep'/'parameter sweep').tag())
model.java.batch('p1').set('pname', ['d'])
model.java.batch('p1').set('plistarr', ['1 2 3'])
model.java.batch('p1').set('punit', ['mm'])
model.java.batch('p1').set('err', JBoolean(True))
model.java.batch('p1').feature('so1').label('parametric solution')
model.java.batch('p1').feature('so1').set('seq', solution.tag())
model.java.batch('p1').feature('so1').set('psol', sols.tag())
model.java.batch('p1').feature('so1').set('param', [
    '"d","0.001"',
    '"d","0.002"',
    '"d","0.003"',
])
model.java.batch('p1').attach(study.tag())


# Datasets
datasets = model/'datasets'
model.java.result().dataset('dset1').label('electrostatic')
model.java.result().dataset('dset2').label('time-dependent')
model.java.result().dataset('dset3').label('sweep/solution')
model.java.result().dataset('dset3').comments(
    'This auto-generated feature could be removed, as it is not '
    'really needed. It was left in the model for the purpose of '
    'testing MPh. Its name contains a forward slash, which MPh '
    'uses to denote parent–child relationships in the node hierarchy.\n')
model.java.result().dataset('dset4').label('parametric sweep')


# Tables

model.java.result().table().create('tbl1', 'Table')
model.java.result().table('tbl1').label('electrostatic')
model.java.result().table().create('tbl2', 'Table')
model.java.result().table('tbl2').label('time-dependent')
model.java.result().table().create('tbl3', 'Table')
model.java.result().table('tbl3').label('parametric')


# Evaluations

model.java.result().numerical().create('gev1', 'EvalGlobal')
model.java.result().numerical('gev1').set('probetag', 'none')
model.java.result().numerical('gev1').label('electrostatic')
model.java.result().numerical('gev1').set('table', 'tbl1')
model.java.result().numerical('gev1').set('expr',  ['2*es.intWe/U^2'])
model.java.result().numerical('gev1').set('unit',  ['pF'])
model.java.result().numerical('gev1').set('descr', ['capacitance'])
model.java.result().numerical('gev1').setResult()

model.java.result().numerical().create('gev2', 'EvalGlobal')
model.java.result().numerical('gev2').set('data', 'dset2')
model.java.result().numerical('gev2').set('probetag', 'none')
model.java.result().numerical('gev2').label('time-dependent')
model.java.result().numerical('gev2').set('table', 'tbl2')
model.java.result().numerical('gev2').set('expr',  ['2*ec.intWe/U^2'])
model.java.result().numerical('gev2').set('unit',  ['pF'])
model.java.result().numerical('gev2').set('descr', ['capacitance'])
model.java.result().numerical('gev2').setResult()

model.java.result().numerical().create('gev3', 'EvalGlobal')
model.java.result().numerical('gev3').set('data', 'dset4')
model.java.result().numerical('gev3').set('probetag', 'none')
model.java.result().numerical('gev3').label('parametric')
model.java.result().numerical('gev3').set('table', 'tbl3')
model.java.result().numerical('gev3').set('expr',  ['2*ec.intWe/U^2'])
model.java.result().numerical('gev3').set('unit',  ['pF'])
model.java.result().numerical('gev3').set('descr', ['capacitance'])
model.java.result().numerical('gev3').setResult()


# Plots
plots = model/'plots'
plots.java.setOnlyPlotWhenRequested(True)

plot = plots.create('PlotGroup2D', name='electrostatic field')
plot.property('titletype', 'manual')
plot.property('title', 'Electrostatic field')
plot.property('showlegendsunit', True)
surface = plot.create('Surface', name='field strength')
surface.property('resolution', 'normal')
surface.property('expr', 'es.normE')
contour = plot.create('Contour', name='equipotentials')
contour.property('number', 10)
contour.property('coloring', 'uniform')
contour.property('colorlegend', False)
contour.property('color', 'gray')
contour.property('resolution', 'normal')

plot = plots.create('PlotGroup2D', name='time-dependent field')
plot.property('data', (datasets/'time-dependent').tag())
plot.property('titletype', 'manual')
plot.property('title', 'Time-dependent field')
plot.property('showlegendsunit', True)
surface = plot.create('Surface', name='field strength')
surface.property('expr', 'ec.normE')
surface.property('resolution', 'normal')
contour = plot.create('Contour', name='equipotentials')
contour.property('expr', 'V_ec')
contour.property('number', 10)
contour.property('coloring', 'uniform')
contour.property('colorlegend', False)
contour.property('color', 'gray')
contour.property('resolution', 'normal')

plot = plots.create('PlotGroup1D', name='evolution')
plot.property('data', (datasets/'time-dependent').tag())
plot.property('titletype', 'manual')
plot.property('title', 'Evolution of field over time')
plot.property('xlabel', 't (s)')
plot.property('xlabelactive', True)
plot.property('ylabel', '|E| (V/m)')
plot.property('ylabelactive', True)
graph = plot.create('PointGraph', name='medium 1')
graph.java.selection().named((selections/'probe 1').tag())
graph.property('expr', 'ec.normE')
graph.property('linecolor', 'blue')
graph.property('linewidth', 3)
graph.property('linemarker', 'point')
graph.property('markerpos', 'datapoints')
graph.property('legend', True)
graph.property('legendmethod', 'manual')
graph.property('legends', ['medium 1'])
graph = plot.create('PointGraph', name='medium 2')
graph.java.selection().named((selections/'probe 2').tag())
graph.property('expr', 'ec.normE')
graph.property('linecolor', 'red')
graph.property('linewidth', 3)
graph.property('linemarker', 'point')
graph.property('markerpos', 'datapoints')
graph.property('legend', True)
graph.property('legendmethod', 'manual')
graph.property('legends', ['medium 2'])

plot = plots.create('PlotGroup2D', name='sweep')
plot.property('data', (datasets/'parametric sweep').tag())
plot.property('titletype', 'manual')
plot.property('title', 'Parameter sweep')
plot.property('showlegendsunit', True)
surface = plot.create('Surface', name='field strength')
surface.property('expr', 'ec.normE')
surface.property('resolution', 'normal')
contour = plot.create('Contour', name='equipotentials')
contour.property('expr', 'V_ec')
contour.property('number', 10)
contour.property('coloring', 'uniform')
contour.property('colorlegend', False)
contour.property('color', 'gray')
contour.property('resolution', 'normal')


# Exports
exports = model/'exports'

data = exports.create('Data', name='data')
data.property('expr', ['es.Ex', 'es.Ey', 'es.Ez'])
data.property('unit', ['V/m', 'V/m', 'V/m'])
data.property('descr', ['x-component', 'y-component', 'z-component'])
data.property('filename', 'data.txt')

image = exports.create('Image', name='image')
image.property('sourceobject', (plots/'electrostatic field').tag())
image.property('pngfilename', 'image.png')
image.property('size', 'manualweb')
image.property('unit', 'px')
image.property('height', '720')
image.property('width', '720')
image.property('lockratio', 'off')
image.property('resolution', '96')
image.property('antialias', 'on')
image.property('zoomextents', 'off')
image.property('fontsize', '12')
image.property('customcolor', array([1, 1, 1]))
image.property('background', 'color')
image.property('gltfincludelines', 'on')
image.property('title1d', 'on')
image.property('legend1d', 'on')
image.property('logo1d', 'on')
image.property('options1d', 'on')
image.property('title2d', 'on')
image.property('legend2d', 'on')
image.property('logo2d', 'off')
image.property('options2d', 'on')
image.property('title3d', 'on')
image.property('legend3d', 'on')
image.property('logo3d', 'on')
image.property('options3d', 'off')
image.property('axisorientation', 'on')
image.property('grid', 'on')
image.property('axes1d', 'on')
image.property('axes2d', 'on')
image.property('showgrid', 'on')
image.property('target', 'file')
image.property('qualitylevel', '92')
image.property('qualityactive', 'off')
image.property('imagetype', 'png')
image.property('lockview', 'off')


# Save
model.save('capacitor.mph')

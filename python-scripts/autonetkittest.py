import autonetkit
anm = autonetkit.NetworkModel();

g_in = anm.add_overlay("input");
nodes = ['r1', 'r2', 'r3', 'r4', 'r5'];

g_in.add_nodes_from(nodes);
g_in.update(device_type = "router", asn=1)
g_in.update("r5", asn=2)

positions = {'r1': (10,79),
	'r2': (226, 25),
	'r3': (172, 295),
	'r4': (334, 187),
	'r5': (496, 349)}

for n in g_in:
	n.x, n.y = positions[n]

autonetkit.update_http(anm)


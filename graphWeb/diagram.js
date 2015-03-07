var width = 1024;
var height = 768;
var radius = 20;

var color = d3.scale.category10();

var force = d3.layout.force()
    .charge(-1000)
    .linkDistance(200)
    .size([width, height]);

var svg = d3.select("#diagram");

d3.json("topology.json", function(json) {
    force
        .nodes(json.nodeList)
        .links(json.linksList)
        .start();

    //var drag = d3.behavior.drag()
    //    .on("drag",function(){d3.select(this).attr("cx",d3.event.x).attr("cy",d3.event.y);tick();});
        //.origin(function(d) { return d; })
        //.on("drag", dragmove);

    var node_drag = d3.behavior.drag()
        .on("dragstart", dragstart)
        .on("drag", dragmove)
        .on("dragend", dragend);

    function dragstart(d, i) {
        force.stop() // stops the force auto positioning before you start dragging
    }

    function dragmove(d, i) {
        d.px += d3.event.dx;
        d.py += d3.event.dy;
        d.x += d3.event.dx;
        d.y += d3.event.dy; 
        tick(); // this is the key to make it work together with updating both px,py,x,y on d !
    }

    function dragend(d, i) {
        d.fixed = true; // of course set the node to fixed so the force doesn't include the node in its auto positioning stuff
        tick();

        force.stop();
    }

    var links = svg.append("g").selectAll("line.link")
        .data(force.links())
        .enter().append("line")
        .attr("class", "link")
        .attr("marker-end", "url(#arrow)");

    var nodes = svg.selectAll("circle.node")
        .data(force.nodes())
        .enter().append("circle")
        .attr("class", "node")
        .attr("r", radius)
        .style("fill", "steelblue")
        .call(node_drag);      

    nodes.append("text")
        .text(function(d) { return d.hostname; });

    force.on("tick", function() {
        links.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        nodes.attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });
    });

    function tick() {
        links.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });

        nodes.attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });
    };

    
});
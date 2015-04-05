var width = 1200;
var height = 800;
var radius = 20;

var force = d3.layout.force()   //Defines the elements of forces in the simulation, charges ensure that nodes (routers) do not overlap
    .charge(-2000)   //charge defines how nodes interact with one another, negative charges causes repulsion
    .linkDistance(200)  //distance between nodes at page load
    .size([width, height]); //Defines the boundries of physics simulation

var svg = d3.select("#diagram"); //Variable to hold the svg element containing the diagram

d3.json("topology.json", function(json) {
    //function extracts the json topology file and inserts it into physics simulation
    force
        .nodes(json.nodeList)
        .links(json.linksList)
        .start(); //starts physics to obtain non-overlapping diagram

    var node_drag = d3.behavior.drag()  //defines dragging behaviour of nodes
        .on("dragstart", dragstart)
        .on("drag", dragmove)
        .on("dragend", dragend);

    function dragstart(d, i) {
        force.stop() // stops auto positioning before dragging behaviour starts
    }

    function dragmove(d, i) {
        //updates x and y of nodes to match location of mouse
        d.px += d3.event.dx;
        d.py += d3.event.dy;
        d.x += d3.event.dx;
        d.y += d3.event.dy; 
        //force.tick(); // Function to update links to match nodes in real-time with drag (Performance hit)
    }

    function dragend(d, i) {
        force.start();
        updatePosition(); //Updates node location to match mouse stopping location
        force.stop(); //Turns off forces as no longer required - 
    }

    // Define the div for the tooltip
    var div = d3.select("body").append("div")   
    .attr("class", "tooltip")               
    .style("opacity", 0);

    var link = svg.selectAll(".link")
      .data(force.links())  //uses the links json defined earlier
    .enter().append("line") //appends visual line
    .attr("marker-end", "url(#stub)")   //defined in html
    .attr("class", "link")
    .style("stroke", "grey")
    .style("stroke-width", 4)   //Adds a stroke making the hover-over easier
    .on("mouseover", function(d) {      
            div.transition()    //transition for the hover-over        
                .duration(10) //short duration to improve responsibility     
                .style("opacity", .9);      
            div .html(d.srcRouter + ' Interface: <b>' + d.srcPort + "</b><br/>" + d.dstRouter + ' Interface: <b>' + d.dstPort + '</b>')  //Displays the interface information for the links
                .style("left", (d3.event.pageX) + "px")     //sets the location of the div for the tooltip
                .style("top", (d3.event.pageY - 28) + "px");    
            })                  
        .on("mouseout", function(d) { //function for the event where mouse is moved away from a link 
            div.transition()        
                .duration(500)      
                .style("opacity", 0);   
        });


    var nodes = svg.selectAll("g")  //nodes defines a grouping of node 'circle' and hostname
                    .data(force.nodes(), function(d, i) { return d + i;})   //d + 1 required otherwise node 0 is skipped
                    .enter()
                    .append("g");

    nodes.append("path")
            //Symbols used for display of router or switch
            .attr("d", d3.svg.symbol()
                .type(function(d) { 
                    if (d.deviceType == 'Router'){
                        return d3.svg.symbolTypes[0];
                        //0 returns a circle, 3 returns a square
                    }
                    else{
                        return d3.svg.symbolTypes[3]; 
                    } 
                })
                .size(2056)
            )
            .style("fill", "steelblue")
            .call(node_drag);

    nodes.append("text")    //appends hostname to node group
        .attr("x", 1)
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .style("font-family","sans-serif")
        .style("fill","white")
        .attr("pointer-events", "none") //Disables mouse turning to Text mode
        .text(function(d) { return d.hostname; });

    force.on("tick", function() {   //tick function defines what the simulation does over time
        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });
        
        nodes.attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
        });

    });

    function updatePosition() { //Manually updates the position of a selected node
        link.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });

        nodes.attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
        });
    };
});
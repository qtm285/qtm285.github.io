window.RevealSVGZoom = window.RevealSVGZoom || {
  id: 'RevealSVGZoom',
  init: function (deck) {
    initRevealSVGZoom(deck);
  }
};

const initRevealSVGZoom = function (Reveal) {
  const zoomconfig = Reveal.getConfig().svgzoom;
  var addZoom = function(zoomOn, zoomFor) { 
    // This selection.nodes().map(d3.select).forEach(d=>...) works,
    // but it seems like something less convoluted should too.
    // What is it that selection.each(d=>...) does instead?
    zoomOn.nodes().map(d3.select).forEach(d=> { 
      d.call(d3.zoom()
       .scaleExtent([1, zoomconfig['max-zoom-factor']])
       .translateExtent([[0, 0], [d.node().viewBox.baseVal.width, d.node().viewBox.baseVal.height]])
       .on("zoom", ({transform}) => { 
          zoomFor(d).selectAll('g.svg-zoom')
                    .attr("transform", transform)
      }))
    })
  }
  
  var onSlide = function(slide) {
    if(zoomconfig['linked-by-default']) {
      unlinked = d3.select(slide).selectAll('.free-zoom svg')
      linked = d3.select(slide).selectAll('svg:not(.free-zoom svg)')
    } else {
      unlinked = d3.select(slide).selectAll('svg:not(.linked-zoom svg)')
      linked = d3.select(slide).selectAll('.linked-zoom svg')
    }
    addZoom(unlinked, d => d)
    addZoom(linked,   d => linked)
  }
  
  Reveal.addEventListener('slidechanged', function (event) { onSlide(event.currentSlide); });
  window.addEventListener('load', function () { onSlide(Reveal.getCurrentSlide()); });
};

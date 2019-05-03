function load_json(path) {
    return fetch(path).then(response => response.json());
}

function load_jsons(paths) {
    var ps = [];
    for(let path of paths) {
        ps.push(fetch(path).then(response => response.json()));
    }
    return Promise.all(ps);
}

function polygonArea(points) { 
    area = 0;         // Accumulates area in the loop
    j = points.length-1;  // The last vertex is the 'previous' one to the first

    for (i=0; i<points.length; i++)
    {
        area = area +  (points[j][0]+points[i][0]) * (points[j][1]-points[i][1]); 
        j = i;  //j is previous vertex to i
    }
    return area/2;
}

var getCentroid2 = function (arr) {
    var twoTimesSignedArea = 0;
    var cxTimes6SignedArea = 0;
    var cyTimes6SignedArea = 0;

    var length = arr.length

    var x = function (i) { return arr[i % length][0] };
    var y = function (i) { return arr[i % length][1] };

    for ( var i = 0; i < arr.length; i++) {
        var twoSA = x(i)*y(i+1) - x(i+1)*y(i);
        twoTimesSignedArea += twoSA;
        cxTimes6SignedArea += (x(i) + x(i+1)) * twoSA;
        cyTimes6SignedArea += (y(i) + y(i+1)) * twoSA;
    }
    var sixSignedArea = 3 * twoTimesSignedArea;
    return [ cxTimes6SignedArea / sixSignedArea, cyTimes6SignedArea / sixSignedArea];        
}
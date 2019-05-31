function load_location_data() {
    return load_json('data/text-blocks.json').then(text_blocks => {
        return text_blocks;
    });
}

// returns [{name: , box: }]
function search_locations(location_data, bbox, text, max_distance = 4) {
    var results = [];
    for(var idx = 0; idx < location_data.length; idx++) {
        var q = location_data[idx];
        if(levenshteinDistance(q[1], text) < max_distance) {
            if(bbox == null || bbox.intersects(q[0])) {
                results.push({"name": q[1], "box": q[0]});
            }
        }
    }
    return results;
}
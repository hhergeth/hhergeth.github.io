function load_location_data() {
    return load_json('data/text-blocks.json').then(text_blocks => {
        return text_blocks;
    });
}

// returns [{name: , box: }]
async function search_locations(location_data, query_box, query_text, max_distance = -1, use_historic = true, use_osm = true, overpass_query = "place") {
    var results = [];

    if(use_historic) {
        for(var idx = 0; idx < location_data.length; idx++) {
            var q = location_data[idx];
            var box = q[0];
            if(max_distance == -1 || levenshteinDistance(q[1], query_text) < max_distance) {
                if(query_box == null || query_box.intersects(box)) {
                    results.push({"name": q[1], "center": [(box[0][0] + box[1][0]) / 2, (box[0][1] + box[1][1]) / 2]});
                }
            }
        }
    }

    if(query_box == null || query_box.getSouthWest().distanceTo(query_box.getNorthEast()) > 250 * 1000) {//distanceTo gives meters
        alert("Trying to query OSM for a very large area -> bad idea!");
        return results;
    }

    if(use_osm) {
        var bounds = query_box == null ? "" : query_box.getSouth() + ',' + query_box.getWest() + ',' + query_box.getNorth() + ',' + query_box.getEast();
        var nodeQuery = 'node[' + overpass_query + '](' + bounds + ');';
        var query = '?data=[out:json][timeout:25];(' + nodeQuery + ');out body;>;out skel qt;';
        var baseUrl = 'http://overpass-api.de/api/interpreter';
        var data = await fetch(baseUrl + query).then(response => response.json());
        var translit = cyrillicToTranslit();
        for(let el of data.elements) {
            var center = [el.lat, el.lon];
            var matching_name = null;
            for(var tag in el.tags) {
                if(tag.startsWith("name")) {
                    var name = translit.transform(el.tags[tag]);
                    if(max_distance == -1 || levenshteinDistance(name, query_text) < max_distance) {
                        matching_name = name;
                        break;
                    }
                }
            }
            if(matching_name) {
                if("name:de" in el.tags)
                    matching_name = el.tags["name:de"];//prefer the german name for readability
                results.push({"name": matching_name, "center": center});
            }
        }
    }

    return results;
}
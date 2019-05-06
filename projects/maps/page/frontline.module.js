//returns {date:, charts: }
//mode can either be 'before' or 'after'
function closest_front(total, front, date, front_name, mode) {
    //extract the relevant charts
    obj = {'date': front.date, 'charts': []};
    for(let chart of front.charts) {
        if(chart.fronts.indexOf(front_name) > -1)
            obj.charts.push(chart);
    }

    if(obj.charts.length == 0)
        return total;

    var date_new_front = new Date(front.date);

    if(mode == 'before')
        if(date < date_new_front)
            return total;
    else if(mode == 'after')
        if(date > date_new_front)
            return total;
    else console.log('invalid mode for closest_front: ' + mode);

    if(total == null)
        return obj;
    var date_total_front = new Date(total.date);
    var difference_ms_new = date - date_new_front;
    var difference_ms_total = date - date_total_front;
    return difference_ms_new < difference_ms_total ? obj : total;
}

function load_frontline_data() {
    return load_json('data/frontline/frontline.json').then(frontlines => {
        var paths = [];
        for(let frontline_file of frontlines) {
            paths.push('data/frontline/' + frontline_file.filename);
        }
        return load_jsons(paths).then(data => {
            frontline_data = [];
            for (var idx = 0; idx < frontlines.length; idx++) {
                frontline_data.push(data[idx]);
            }
            return frontline_data;
        });
    });
}
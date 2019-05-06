function validate_person_data(person_data) {
    var found_error = false;

    for (var person_name in person_data) {
        var places = person_data[person_name].places;
        var route = person_data[person_name].route;

        for(var idx = 0; idx < route.length; idx++) {
            if(!(route[idx].place in places)) {
                found_error = true;
                console.log(person_name + " :: " + route[idx].place + " not in places!");
            }

            if(idx < route.length - 1) {
                var date1 = route[idx + 0].date;
                var date2 = route[idx + 1].date;
                if(new moment(date1, 'DD.MM.YYYY').isAfter(new moment(date2, 'DD.MM.YYYY'))) {
                    found_error = true;
                    console.log(person_name + " :: " + date1 + " after " + date2);
                }
            }
        }
    }

    if(found_error)
        alert("Found errors in the person data, please check the console!");
}

function load_person_data() {
    return load_json('data/persons/persons.json').then(persons => {
        var paths = [];
        for(let person of persons){
            paths.push('data/persons/' + person.folder + '/places.json');
            paths.push('data/persons/' + person.folder + '/route.json');
        }
        return load_jsons(paths).then(data => {
            person_data = {};

            for (var idx = 0; idx < persons.length; idx++) {
                person_data[persons[idx].name] = {'places': data[2 * idx + 0], 'route': data[2 * idx + 1]};
            }

            validate_person_data(person_data);
            return person_data;
        })
    });
}
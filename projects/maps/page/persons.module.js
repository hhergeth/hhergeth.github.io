function validate_person_data() {
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
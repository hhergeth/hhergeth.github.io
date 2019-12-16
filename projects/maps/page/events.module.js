function load_event_data() {
    return load_json('data/events.json').then(events => {
        return events;
    });
}
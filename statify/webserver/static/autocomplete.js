function setupAutocompleteRow(item, data) {
    item.innerHTML = document.querySelector('#autocomplete-template').innerHTML;
    item.querySelector('.ac-row')
        .setAttribute('data-spotify-id', data.spotify_id);
    item.querySelector('.ac-cover').setAttribute('src', data.cover_url);
    item.querySelector('.ac-name').textContent = data.name;
    item.querySelector('.ac-artists').textContent = data.artists_names;
}


document.addEventListener('DOMContentLoaded', function() {
    let host = window.location.origin;
    new autoComplete({
        data: {
            src: async (query) => {
                let source = await fetch(
                    `${host}/api/autocomplete?query=${query}`
                );
                let data = await source.json();
                return data;
            },
            keys: ['name', 'artist'],
        },
        resultsList: {
            class: 'resultList',
        },
        resultItem: {
            element: (item, data) => {
                return setupAutocompleteRow(item, data.value)
            }
        },
        searchEngine: (query, value) => { return value; },
        events: {
            list: {
                click: (event) => {
                    let spotifyId = event.target.closest('.ac-row').getAttribute(
                        'data-spotify-id'
                    );
                    window.location = `${host}/song/${spotifyId}`;
                }
            }
        },
        debounce: 200,
    });
});
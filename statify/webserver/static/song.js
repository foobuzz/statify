function initSongChart(spotifyId) {
    fetch(`/api/listenings/${spotifyId}`).then(function(response) {
        response.text().then(function(text) {
            listenings = JSON.parse(text);
            timeData = convertListeningsToTimeSeries(listenings);
            const config = {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        data: timeData,
                        label: "# Listenings",
                        borderColor: "#3e95cd",
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        x: {
                            type: 'time'
                        }
                    },
                    maintainAspectRatio: false,
                }
            };
            const myChart = new Chart(
                document.getElementById('songChart'),
                config,
            );
        });
    });
}


function convertListeningsToTimeSeries(listenings) {
    let timeData = [];
    listenings.forEach(function(listening, index) {
        timeData.push({
            x: new Date(listening.played_at * 1000),
            y: index + 1,
        });
    });
    return timeData;
}


function setupAutocompleteRow(item, data) {
    item.innerHTML = document.querySelector('#autocomplete-template').innerHTML;
    item.querySelector('.ac-row')
        .setAttribute('data-spotify-id', data.spotify_id);
    item.querySelector('.ac-cover').setAttribute('src', data.cover_url);
    item.querySelector('.ac-name').textContent = data.name;
    item.querySelector('.ac-artists').textContent = data.artists_names;
}


document.addEventListener('DOMContentLoaded', function() {
    initSongChart(JS_INIT_DATA.spotifyId);

    let host = window.location.origin;

    const autoCompleteJS = new autoComplete({
        data: {
            src: async (query) => {
                const source = await fetch(
                    `${host}/api/autocomplete?query=${query}`
                );
                const data = await source.json();
                return data;
            },
            keys: ['name', 'artist'],
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

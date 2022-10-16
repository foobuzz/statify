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


document.addEventListener('DOMContentLoaded', function() {
    initSongChart(JS_INIT_DATA.spotifyId);

    const autoCompleteJS = new autoComplete({
        data: {
            src: async (query) => {
                const source = await fetch(`${window.location.origin}/api/autocomplete?query=${query}`);
                const data = await source.json();
                return data;
            },
            keys: ['name', 'artist'],
        },
        resultItem: {
            element: (item, data) => {
                item.setAttribute('data-spotify-id', data.value.spotify_id);
                item.textContent = [
                    data.value.artists_names, data.value.name,
                ].join(' - ');
            }
        },
        searchEngine: (query, value) => { return value; },
        events: {
            list: {
                click: (event) => {
                    console.log(event.target);
                    let spotifyId = event.target.getAttribute('data-spotify-id');
                    window.location = `${window.location.origin}/song/${spotifyId}`;
                }
            }
        },
        debounce: 500,
    });
});

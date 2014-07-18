var messageContainer = $('.output'),
    sparkline_options = {
        curveType: 'function',
        interpolateNulls: true,
        legend: {
            position: 'none'
        },
        axisTitlesPosition: 'none',
        titlePosition: 'none',
        hAxis: {
            'baselineColor': 'none',
            'textPosition': 'none',
            'gridlines': {
                'count': 0
            }
        },
        vAxis: {
            'baselineColor': 'none',
            'textPosition': 'none',
            'gridlines': {
                'count': 0
            }
        },
        tooltip: {
            trigger: 'none'
        },
        chartArea: {
            'width': '100%',
            'height': '100%'
        }
    },
    reconnect_in = 2;

openWebSocket();
google.setOnLoadCallback(drawCharts);
recentBlogPosts();
var blog = window.setInterval(recentBlogPosts, 10000);

// Make sure that graphs resize nicely with the window.
$(window).resize(function () {
    drawCharts();
});

// Draw out Google Charts
function drawCharts() {
    Object.keys(sparkline_data).forEach(function (key) {
        var chart = new google.visualization.LineChart(document.getElementById(key));
        chart.draw(sparkline_data[key], sparkline_options);
    });
}

// Look after the WebSockets connection and messages
function openWebSocket() {
    if ("WebSocket" in window) {
        var url = "ws://127.0.0.1:8080/ws/",
            ws = new WebSocket(url);

        messageContainer.html('WebSocket are supported by your Browser!');

        console.log(ws.readyState);
        ws.onopen = function () {
            messageContainer.html('Connected');
            console.log(ws.readyState);
            reconnect_in = 2;
        };

        ws.onmessage = function (evt) {
            var received_msg = evt.data,
                data = $.parseJSON(received_msg),
                d = new Date(data.datetime * 1000),
                curr_hour = d.getHours(),
                curr_min = d.getMinutes(),
                spark_ref = "spark_" + data.service + "_" + data.user_account;

            messageContainer.html(messageContainer.html() + '<br />' + received_msg);

            // Update follower count below sparkline
            $('#' + data.service + "_" + data.user_account + " .count").html(data.followers);
            $('.' + data.service + " #last_updated").html(curr_hour + ":" + curr_min);

            if (sparkline_data[spark_ref].getNumberOfRows <= 40) {
                sparkline_data[spark_ref].removeRow(39);
            }
            sparkline_data[spark_ref].insertRows(0, [[new Date(data.datetime * 1000), data.followers]]);

            drawCharts();
        };

        ws.onclose = function () {
            messageContainer.html('Lost connection with the server. Attempting reconnect in ' + reconnect_in + ' seconds.');
            setTimeout(function() {
                openWebSocket();
            }, reconnect_in * 1000);
            reconnect_in = reconnect_in * 2;
        };

        ws.onerror = function(err) {
            console.error('Socket encountered error: ', err.message, 'Closing socket');
            ws.close();
        };

    } else {
        messageContainer.html('WebSocket are NOT supported by your Browser.');
    }
}

function recentBlogPosts() {

    $.getJSON( "http://www.vam.ac.uk/blog/api/get_recent_posts/", function( data ) {
        var items = [];
        $.each (data.posts, function (key, data) {
            if (key <= 4) {
                items.push(
                        '<div class="account" id="post_' + data.id + '">' +
                        '<div class="thumbnail_image" style="background-image: url(\'' + data.attachments[0].url.replace('http://www.vam.ac.uk/blog', 'https://s3-eu-west-1.amazonaws.com/vam-blog') + '\');"></div>' +
                        '<h2>' + data.title_plain + '</h2>' +
                        '<time>' + new Date(data.date) + '</time>' +
                        '</div>'
                );
            }
        });

        $('.wordpress .blog_posts').remove();

        $( "<div/>", {
            "class": "blog_posts",
            html: items.join( "" )
        }).insertAfter( ".wordpress h1" );
    });
}